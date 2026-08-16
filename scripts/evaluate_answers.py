"""Grade the agent's answers, not just its retrieval.

Run from the repository root:

    python -m scripts.evaluate_answers          # all 27 cases
    python -m scripts.evaluate_answers 5        # first 5, for a quick check

`scripts/evaluate.py` asks whether the right sections arrived. This asks whether
the answer built on them was right — a different question with a different
failure mode, since a model can reach a correct answer from the wrong sections
or a wrong one from the right sections.

Grading is done by a stronger model than the one answering (see JUDGE_MODEL).
That asymmetry matters: a judge no more capable than what it grades mostly
agrees with it. Costs roughly USD 0.75 for a full run, so it is a per-change
check rather than something to sit in a loop.
"""

import concurrent.futures as futures
import io
import sys

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import ToolMessage
from pydantic import BaseModel, Field

from app.agent import build_agent
from app.config import JUDGE_MODEL
from tests.eval_cases import CASES, REFUSAL_CASES

# API calls, so this is bound by latency rather than CPU. Kept modest to stay
# clear of rate limits — each worker runs an agent turn and a judge call.
WORKERS = 4

JUDGE_PROMPT = """You are grading a handbook assistant's answer.

The assistant answers employee questions about a company handbook using a search
tool. It is required to cite the sections it used, in the form [HR-004 §3.1].

QUESTION
{question}

WHAT A CORRECT ANSWER MUST CONVEY
{expected}

THE ASSISTANT'S ANSWER
{actual}

THE HANDBOOK TEXT THE ASSISTANT RETRIEVED
{context}

Grade three things independently. An answer can be correct but uncited, or
well-cited but wrong, and those are different defects.

correct — does the answer convey what the expected answer requires? Judge the
substance, not the wording, and not the extra detail. Where the expected answer
says the assistant must NOT say something, saying it is a failure even if the
rest is right. An answer that gives the right figure but omits a qualifier the
expected answer calls for is not correct.

grounded — is every factual claim supported by the retrieved text above? A
figure, date, or rule that does not appear there is fabricated, even if it
happens to be true.

cited — are there citations, do they name sections that appear in the retrieved
text, and do those sections actually support the claims they are attached to?

Then give one sentence saying what decided it. Name the specific error if there
is one."""


class Verdict(BaseModel):
    """One graded answer."""

    correct: bool = Field(description="Conveys what the expected answer requires")
    grounded: bool = Field(description="Every claim is supported by retrieved text")
    cited: bool = Field(description="Citations are present, real, and apposite")
    reason: str = Field(description="One sentence on what decided it")


def run_agent(agent, question: str) -> tuple[str, str]:
    """Ask one question. Returns (answer, the handbook text it retrieved).

    No conversation history — each case is independent, so a mistake on one
    cannot bleed into the next.
    """
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    messages = result["messages"]

    # Tool messages hold the formatted chunks. The judge needs them to tell a
    # fabricated figure from one that was actually retrieved.
    context = "\n\n".join(
        message.content
        for message in messages
        if isinstance(message, ToolMessage)
    )
    return messages[-1].text, context or "(no search was performed)"


def grade(agent, judge, case: dict) -> tuple[dict, str, Verdict]:
    answer, context = run_agent(agent, case["question"])
    verdict = judge.invoke(
        JUDGE_PROMPT.format(
            question=case["question"],
            expected=case["answer"],
            actual=answer,
            context=context,
        )
    )
    return case, answer, verdict


def report(results: list, title: str, score_citations: bool) -> tuple[int, int]:
    """Print one section. Returns (passed, total)."""
    print(f"\n{title}")
    passed = 0

    for case, _answer, verdict in results:
        # Refusals cite nothing and retrieve nothing, so only correctness is
        # meaningful there — scoring them on citations would fail every one.
        flags = [verdict.correct]
        if score_citations:
            flags += [verdict.grounded, verdict.cited]

        ok = all(flags)
        passed += ok

        marks = "".join(
            letter if flag else "-"
            for letter, flag in zip("cgx", flags)
        )
        print(f"  {'PASS' if ok else 'FAIL'} [{marks:3}]  {case['question'][:52]}")
        if not ok:
            print(f"              {verdict.reason}")

    return passed, len(results)


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

    answerable = CASES[:limit] if limit else CASES
    refusals = REFUSAL_CASES[:limit] if limit else REFUSAL_CASES

    agent = build_agent()

    # with_structured_output forces the judge to fill in the Verdict schema
    # rather than writing prose we would then have to parse.
    judge = ChatAnthropic(
        model=JUDGE_MODEL, max_tokens=2000
    ).with_structured_output(Verdict)

    print(f"Grading {len(answerable) + len(refusals)} cases with {JUDGE_MODEL}...")

    with futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        # Submitted together, collected in order, so output is stable between
        # runs even though the work is not.
        answerable_results = list(
            pool.map(lambda c: grade(agent, judge, c), answerable)
        )
        refusal_results = list(
            pool.map(lambda c: grade(agent, judge, c), refusals)
        )

    a_passed, a_total = report(
        answerable_results, "Answerable  [c]orrect [g]rounded [x]cited",
        score_citations=True,
    )
    r_passed, r_total = report(
        refusal_results, "Should decline  [c]orrect", score_citations=False,
    )

    correct = sum(v.correct for _, _, v in answerable_results)
    grounded = sum(v.grounded for _, _, v in answerable_results)
    cited = sum(v.cited for _, _, v in answerable_results)

    print(f"\nAnswerable   {a_passed}/{a_total} fully passed")
    print(f"  correct    {correct}/{a_total}")
    print(f"  grounded   {grounded}/{a_total}")
    print(f"  cited      {cited}/{a_total}")
    print(f"Declined     {r_passed}/{r_total}")


if __name__ == "__main__":
    main()