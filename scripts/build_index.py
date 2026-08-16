"""Rebuild the Chroma index from `corpus/`.

Run from the repository root:

    python -m scripts.build_index

Safe to run as often as you like — it wipes the old index and starts clean.
"""

import time

from app.config import CHROMA_DIR, COLLECTION_NAME
from app.rag.ingest import build_index

# Asked after every build so a broken index fails here, loudly, instead of
# quietly returning nothing the first time someone uses the chat UI.
# Taken from tests/retrieval_eval.md rather than invented — a vague query like
# "how much paid time off do I get" matches a dozen sections equally and tells
# you nothing about whether retrieval improved or got worse.
SMOKE_TEST_QUERY = "I've been here three years. How much PTO do I get?"
EXPECTED_TOP_DOC = "HR-004"


def main() -> None:
    started = time.perf_counter()
    store = build_index()
    elapsed = time.perf_counter() - started

    chunk_count = len(store.get()["ids"])
    print(f"Indexed {chunk_count} chunks into '{COLLECTION_NAME}' in {elapsed:.1f}s")
    print(f"Location: {CHROMA_DIR}")

    print(f"\nSmoke test: {SMOKE_TEST_QUERY!r}")
    hits = store.similarity_search_with_score(SMOKE_TEST_QUERY, k=5)
    for document, score in hits:
        label = f"{document.metadata['doc_id']} §{document.metadata['section']}"
        print(f"  {score:.3f}  {label:14} {document.metadata['title']}")

    # Scores are squared L2 distance, not similarity — lower is closer.
    if not any(d.metadata["doc_id"] == EXPECTED_TOP_DOC for d, _ in hits):
        print(f"\n  WARNING: {EXPECTED_TOP_DOC} missing from top 5 — retrieval regressed.")


if __name__ == "__main__":
    main()