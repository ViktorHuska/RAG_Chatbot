"""Score retrieval against the graded questions in `tests/retrieval_eval.md`.

Run from the repository root:

    python -m scripts.evaluate          # uses TOP_K from config
    python -m scripts.evaluate 5        # override k

This measures ONE thing: did the right chunks come back. It says nothing about
whether the final answer was correct — that needs the model, and a wrong answer
built on the right chunks is a different bug from a wrong answer built on the
wrong ones. Keeping them separate is the whole point of scoring retrieval alone.

Tier 6 (correct refusal) is not scored here. Those questions have no right
answer to retrieve, so they belong to the answer evaluation instead.
"""

import sys

from app.config import TOP_K
from app.rag.retriever import retrieve
from tests.eval_cases import CASES

def matches(chunk_metadata: dict, expected: str) -> bool:
    """Does this chunk satisfy an expectation like `HR-004 3.1`?

    An expectation on a parent section matches its children, so `IT-001 4`
    is satisfied by a chunk from §4.2. Written as an explicit `.` check rather
    than a bare `startswith`, which would let §4 match §41.
    """
    doc_id, _, section = expected.partition(" ")
    if chunk_metadata["doc_id"] != doc_id:
        return False
    found = chunk_metadata["section"]
    return found == section or found.startswith(section + ".")


def rank_of(hits: list, group: list[str]) -> int | None:
    """Position (1-based) of the first hit satisfying any entry in the group."""
    for position, hit in enumerate(hits, start=1):
        if any(matches(hit.metadata, expected) for expected in group):
            return position
    return None


def main() -> None:
    k = int(sys.argv[1]) if len(sys.argv) > 1 else TOP_K

    passed = 0
    groups_found = groups_total = 0
    chunks_delivered = characters_delivered = 0

    for case in CASES:
        question, expect = case["question"], case["expect"]
        documents = retrieve(question, k=k)
        found = [rank_of(documents, group) is not None for group in expect]

        groups_total += len(found)
        groups_found += sum(found)
        chunks_delivered += len(documents)
        characters_delivered += sum(len(d.page_content) for d in documents)

        complete = all(found)
        passed += complete

        shown = " ".join("ok" if f else "--" for f in found)
        print(f"  {'PASS' if complete else 'FAIL'}  [{shown:8}]  {question[:58]}")

    total = len(CASES)
    print(f"\nk = {k}  (search + neighbours + references)")
    print(f"  fully answered   {passed}/{total}  ({passed / total:.0%})")
    print(f"  documents found  {groups_found}/{groups_total}  ({groups_found / groups_total:.0%})")
    # Cost, not quality — but it is the thing the two expansions trade against,
    # so it belongs next to them. No MRR: the pipeline orders chunks by document
    # and position for readability, so position is no longer a relevance rank.
    print(f"  context size     {chunks_delivered // total} chunks, "
          f"{characters_delivered // total} chars per question")


if __name__ == "__main__":
    main()