"""Build the Chroma index from the markdown handbook in `corpus/`.

Pipeline: read files -> split into chunks -> attach metadata -> write to Chroma.
"""

import shutil
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from app.config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    CORPUS_DIR,
)
from app.rag.embeddings import LocalEmbeddings

# Our documents nest three levels deep: `# HR-004`, `## 3. Accrual`,
# `### 3.1 Rates`. Splitting on all three keeps each chunk inside one subsection.
HEADERS_TO_SPLIT_ON = [("#", "h1"), ("##", "h2"), ("###", "h3")]

FRONT_MATTER_DELIMITER = "---"


def parse_front_matter(raw: str) -> tuple[dict[str, str], str]:
    """Split a document's YAML front matter from its markdown body.

    Every handbook document opens with a fenced header:

        ---
        doc_id: HR-004
        title: Paid Time Off and Leave
        ---

        # HR-004 - Paid Time Off and Leave
        ...

    Returns `({"doc_id": "HR-004", ...}, "# HR-004 - ...")`. A document with no
    front matter, or with an unterminated fence, returns `({}, raw)` — the caller
    still gets usable text and can fall back to the filename for identity.
    """
    lines = raw.splitlines()

    # A fence only counts at the very top of the file. `---` is also valid
    # markdown for a horizontal rule, so anywhere else it is body content.
    if not lines or lines[0].strip() != FRONT_MATTER_DELIMITER:
        return {}, raw

    fields: dict[str, str] = {}

    # Start at 1 to skip the opening fence, but keep `index` aligned to the
    # original list so the body slice below is correct.
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONT_MATTER_DELIMITER:
            body = "\n".join(lines[index + 1:]).lstrip("\n")
            return fields, body

        # `partition` splits on the FIRST colon only, so a title containing a
        # colon survives intact. `split(":")` would lose everything after it.
        key, separator, value = line.partition(":")
        if not separator:
            continue  # blank line or malformed entry — skip rather than crash
        fields[key.strip()] = value.strip()

    # Fell off the end without a closing fence. The header is unreliable, so
    # discard it rather than indexing half-parsed values as if they were good.
    return {}, raw


def doc_id_from_filename(path: Path) -> str:
    """Recover a doc_id like `HR-004` from `HR-004-paid-time-off-and-leave.md`."""
    prefix, _, number = path.stem.partition("-")
    number = number.split("-")[0]
    return f"{prefix}-{number}"


def load_documents(corpus_dir: Path = CORPUS_DIR) -> list[Document]:
    """Read every markdown file in the corpus into a LangChain Document.

    One Document per file, still whole — splitting happens later. The front
    matter becomes the Document's metadata, and every chunk cut from this
    Document will inherit a copy of it, which is what makes citations possible.
    """
    documents = []

    for path in sorted(corpus_dir.glob("*.md")):
        fields, body = parse_front_matter(path.read_text(encoding="utf-8"))

        metadata = {
            # The filename is the fallback if the header is missing or broken.
            "doc_id": fields.get("doc_id") or doc_id_from_filename(path),
            "title": fields.get("title", path.stem),
            "version": fields.get("version", ""),
            "effective": fields.get("effective", ""),
            "owner": fields.get("owner", ""),
            "source": path.name,
        }

        documents.append(Document(page_content=body, metadata=metadata))

    return documents


def section_label(header_metadata: dict[str, str]) -> str:
    """Turn header metadata into a citation number like `3.1`.

    Headings read `### 3.1 Accrual Rates`, so the first word is the number.
    Prefers the deepest heading available, and returns "" for a chunk that sits
    above any numbered section (a document's opening lines, say).
    """
    heading = header_metadata.get("h3") or header_metadata.get("h2") or ""
    return heading.split(" ")[0].rstrip(".")


def split_documents(documents: list[Document]) -> list[Document]:
    """Cut whole documents into chunks small enough to embed precisely.

    Two passes. The first splits on markdown headings, so a chunk boundary lands
    where the topic actually changes. The second is a safety net for sections
    that are still too long after that.
    """
    header_splitter = MarkdownHeaderTextSplitter(
        HEADERS_TO_SPLIT_ON,
        # Keep the heading line inside the chunk text. It is some of the most
        # descriptive wording in the document, so it belongs in the embedding.
        strip_headers=False,
    )
    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    chunks: list[Document] = []

    for document in documents:
        sections = header_splitter.split_text(document.page_content)

        for section in sections:
            # The header splitter only knows about headings, so it returns
            # metadata like {"h2": "3. Accrual"} and has no idea which file this
            # came from. Replace it with the file's metadata plus the section
            # number, so every chunk can be cited on its own.
            section.metadata = {
                **document.metadata,
                "section": section_label(section.metadata),
            }

        document_chunks = size_splitter.split_documents(sections)

        # Where each chunk sits in its document, counting from 0. Retrieval can
        # then pull a hit's neighbours: "Amounts" and "Eligibility" are adjacent
        # sections, and an answer built on the first without the second is
        # confidently wrong. Position is per document, so it only has meaning
        # alongside doc_id.
        for position, chunk in enumerate(document_chunks):
            chunk.metadata["position"] = position

        chunks.extend(document_chunks)

    return chunks


def build_index() -> Chroma:
    """Embed the whole corpus and write it to Chroma, replacing any old index.

    Wipe-and-rebuild rather than update-in-place. The corpus is small enough
    that a full rebuild takes seconds, and it guarantees the index matches the
    files on disk — no chunks left behind from a section that was deleted.
    """
    chunks = split_documents(load_documents())

    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR) # remove chroma embeddings, if any exist already
    CHROMA_DIR.mkdir(parents=True)

    return Chroma.from_documents(
        documents=chunks,
        embedding=LocalEmbeddings(),
        collection_name=COLLECTION_NAME,
        # Chroma writes SQLite files here, so the index survives a restart.
        persist_directory=str(CHROMA_DIR),
    )