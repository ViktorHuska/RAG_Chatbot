"""Search over the built index, exposed as a tool the model can call.

This is the read side of the pipeline. `ingest.py` writes the index once;
everything here only reads it.
"""

import logging
import re
import threading
from collections import defaultdict

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.tools import tool

from app.config import CHROMA_DIR, COLLECTION_NAME, NEIGHBOUR_HITS, TOP_K
from app.rag.embeddings import LocalEmbeddings

logger = logging.getLogger(__name__)

_store: Chroma | None = None
_store_lock = threading.Lock()


def get_store() -> Chroma:
    """Open the existing index, building the client at most once per process.

    Deliberately not `@lru_cache`. The model can request several searches in one
    turn, and LangGraph runs those in a thread pool — `lru_cache` does not hold a
    lock while the function runs, so two threads both miss and both construct a
    Chroma client. The second collides with the first's partly-initialised state
    and fails inside chromadb with an unrelated-looking AttributeError.
    """
    global _store

    # Fast path once built: no lock on the overwhelmingly common case.
    if _store is not None:
        return _store

    with _store_lock:
        # Re-checked inside the lock: another thread may have built it while
        # this one waited.
        if _store is None:
            if not CHROMA_DIR.exists():
                raise FileNotFoundError(
                    f"No index at {CHROMA_DIR}. Run: python -m scripts.build_index"
                )
            _store = Chroma(
                collection_name=COLLECTION_NAME,
                embedding_function=LocalEmbeddings(),
                persist_directory=str(CHROMA_DIR),
            )

    return _store


def expand_with_neighbours(
    hits: list[Document], top: int = NEIGHBOUR_HITS
) -> list[Document]:
    """Add the chunk before and after each of the top hits, from the same document.

    Search ranks chunks independently, so it will happily return "§8.2 Amounts"
    — a table of relocation lump sums — while leaving "§8.3 Eligibility" behind,
    because the question was about moving and §8.3 is written about eligibility.
    An answer built on the first without the second is confidently wrong.

    Handbook documents are written in order: the section that limits a rule sits
    beside the section that states it. Adjacency is a decent proxy for "you need
    to read this too", and checking costs a metadata lookup rather than a search.

    Only the first `top` hits are expanded. Every hit still comes back; the
    lower-ranked ones just arrive without company. Search rank is a usable
    signal for "is this on topic", and the neighbours of an off-topic hit are
    off-topic twice over — paid for in tokens on every turn.
    """
    if not hits:
        return hits

    # Positions already retrieved, so we don't ask Chroma for them again.
    retrieved = {(hit.metadata["doc_id"], hit.metadata["position"]) for hit in hits}

    wanted: dict[str, set[int]] = defaultdict(set)
    for hit in hits[:top]:
        doc_id, position = hit.metadata["doc_id"], hit.metadata["position"]
        for neighbour in (position - 1, position + 1):
            # Negative positions do not exist; positions past the end simply
            # match nothing, so only the lower bound needs guarding.
            if neighbour >= 0 and (doc_id, neighbour) not in retrieved:
                wanted[doc_id].add(neighbour)

    store = get_store()
    neighbours: list[Document] = []

    for doc_id, positions in wanted.items():
        # One query per document rather than one big $or: Chroma needs at least
        # two clauses inside $or, so the single-document case would need special
        # casing. A handful of documents per search makes this cheap either way.
        found = store.get(
            where={
                "$and": [
                    {"doc_id": {"$eq": doc_id}},
                    {"position": {"$in": sorted(positions)}},
                ]
            }
        )
        for text, metadata in zip(found["documents"], found["metadatas"]):
            neighbours.append(Document(page_content=text, metadata=metadata))

    # Read the way the handbook reads: documents in the order search ranked them,
    # sections in the order they appear inside each document. Sorting everything
    # by position alone would bury the best match under whatever preceded it.
    document_rank = {}
    for hit in hits:
        document_rank.setdefault(hit.metadata["doc_id"], len(document_rank))

    return sorted(
        hits + neighbours,
        key=lambda d: (document_rank[d.metadata["doc_id"]], d.metadata["position"]),
    )


# Matches the handbook's own cross-references: `HR-001 §4.3`, `ORG-002 §3`,
# occasionally `HR-002 §§3.3`. 206 of these exist across the corpus.
CITATION = re.compile(r"\b([A-Z]{2,3}-\d{3})\s*§+\s*(\d+(?:\.\d+)*)")

# Ceiling on chunks pulled in this way. Generous because it is a backstop
# against pathological cases, not the scheduler — fairness between references
# is handled by resolving them round-robin below.
MAX_REFERENCED_CHUNKS = 12


def follow_references(
    sources: list[Document], existing: list[Document]
) -> list[Document]:
    """Fetch the sections that the retrieved text explicitly points at.

    Neighbour expansion reaches sideways within a document; this reaches across
    them. The handbook says "at a rate determined by tenure tier, as defined in
    HR-001 §4" — the author already wrote down what you need to read next, so
    following the link beats hoping a second embedding search rediscovers it.

    References are collected from `sources` — the actual search hits — and not
    from neighbour chunks. Neighbours are worth reading but they drag in §1.x
    scope-and-purpose sections, which cite half the handbook as boilerplate;
    letting those compete for the budget starved the references that came from
    the evidence itself. Follow what the evidence cites, not what the padding
    cites.

    Resolution is round-robin: every reference gets its first chunk before any
    gets its second. A precise citation ("ORG-002 §2.3", one chunk) is satisfied
    in the first round and can no longer be locked out by a broad one ("see
    WRK-001 §5", a whole section) that happened to be collected earlier.

    Returns only chunks not already present in `existing`.
    """
    seen = {(d.metadata["doc_id"], d.metadata["section"]) for d in existing}

    # Deduplicated while keeping collection order — dict preserves insertion
    # order, and sources arrive ranked, so earlier hits' references go first.
    references = {}
    for document in sources:
        for doc_id, section in CITATION.findall(document.page_content):
            if (doc_id, section) not in seen:
                references[(doc_id, section)] = None

    if not references:
        return []

    # One fetch per referenced document, reused across that document's
    # references. Documents run ~27 chunks, so pulling all of one is cheap.
    store = get_store()
    cache: dict[str, list[Document]] = {}

    def chunks_of(doc_id: str) -> list[Document]:
        if doc_id not in cache:
            found = store.get(where={"doc_id": doc_id})
            cache[doc_id] = sorted(
                (
                    Document(page_content=text, metadata=metadata)
                    for text, metadata in zip(
                        found["documents"], found["metadatas"]
                    )
                ),
                key=lambda d: d.metadata["position"],
            )
        return cache[doc_id]

    # Each reference becomes a queue of the chunks it names, in document order.
    # `§4` matches §4.1, §4.2 and so on; the explicit dot stops it matching §41.
    queues: list[list[Document]] = []
    for doc_id, section in references:
        matching = [
            chunk
            for chunk in chunks_of(doc_id)
            if (
                chunk.metadata["section"] == section
                or chunk.metadata["section"].startswith(section + ".")
            )
            and (doc_id, chunk.metadata["section"]) not in seen
        ]
        if matching:
            queues.append(matching)

    resolved: list[Document] = []
    while queues and len(resolved) < MAX_REFERENCED_CHUNKS:
        for queue in queues:
            chunk = queue.pop(0)
            key = (chunk.metadata["doc_id"], chunk.metadata["section"])
            # A chunk can sit in two queues when references overlap, as with
            # "ORG-002 §3" alongside "ORG-002 §3.2".
            if key not in seen:
                seen.add(key)
                resolved.append(chunk)
            if len(resolved) >= MAX_REFERENCED_CHUNKS:
                break
        queues = [queue for queue in queues if queue]

    return sorted(
        resolved, key=lambda d: (d.metadata["doc_id"], d.metadata["position"])
    )


def retrieve(query: str, k: int = TOP_K) -> list[Document]:
    """The full retrieval pipeline: search, then widen it twice.

    Search alone ranks chunks in isolation. The two expansions add what the
    corpus itself says belongs alongside a hit — the sections beside it, and the
    sections it points at.

    `search_handbook` and `scripts/evaluate.py` both go through here. If the
    evaluation measured bare `similarity_search`, it would be scoring a system
    the model never uses.
    """
    hits = get_store().similarity_search(query, k=k)
    documents = expand_with_neighbours(hits)

    # Referenced sections go last. What search matched is the primary evidence;
    # these are supporting definitions the text pointed at. References are
    # collected from the hits alone, but deduplicated against everything the
    # neighbour pass already added.
    return documents + follow_references(hits, existing=documents)


def format_chunk(document: Document) -> str:
    """Render one chunk the way the model should read it.

    The citation goes on its own line above the text. The model can only cite
    what it can see, so if the identifier is not in this string, it will either
    omit the citation or invent one.
    """
    metadata = document.metadata
    citation = f"[{metadata['doc_id']} §{metadata['section']}]"
    return f"{citation} {metadata['title']}\n{document.page_content}"


# parse_docstring turns the Args section below into the tool's argument schema,
# so `query` reaches the model with a description instead of a bare "string".
@tool(parse_docstring=True)
def search_handbook(query: str) -> str:
    """Search the Meridian Systems employee handbook.

    Call this before answering any policy question, and call it again whenever
    a result points at something you have not read yet. Handbook documents
    cross-reference each other constantly: a section on PTO will say the rate
    depends on "tenure tier, as defined in HR-001 §4" without stating what the
    tiers are. Answering from the first result alone gives a confidently
    incomplete answer.

    Returns the most relevant sections, each headed by its citation.

    Args:
        query: What to look for, phrased the way the handbook would phrase it
            rather than the way the employee did. "three years at the company"
            should be searched as "tenure tier"; "working from Spain for a
            month" as "work from anywhere", not "business travel". A short
            topic phrase works better than a full question.

            When the question is about the company itself rather than a policy
            — how it is owned, where it operates, what it sells — name the
            company in the query. A bare topic word lands in whichever policy
            uses that word: "stock price" finds the equity-grant policy, while
            "Meridian stock price" finds the company overview that answers it.
    """
    try:
        documents = retrieve(query)
    except Exception:
        # A tool exception propagates up through LangGraph and kills the whole
        # turn — in the server, that is a dead stream for a failure the model
        # could have talked its way around. Returning a string keeps the turn
        # alive; the string is written as an instruction because the model is
        # its reader, and the model's failure mode here would be improvising an
        # answer without the handbook.
        logger.exception("handbook search failed for query %r", query)
        return (
            "The handbook search is temporarily unavailable. Tell the user you "
            "could not check the handbook right now and that they should try "
            "again shortly. Do not answer the question from memory."
        )

    if not documents:
        return "No matching sections found."

    return "\n\n---\n\n".join(format_chunk(document) for document in documents)


