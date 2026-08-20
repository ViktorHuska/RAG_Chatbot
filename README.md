# Meridian Handbook Assistant

An agentic RAG chatbot over a 20,000-word synthetic employee handbook. Ask it
"how much PTO do I get?" and it searches the handbook, follows the
cross-references the handbook itself makes, and answers with section citations
like `[HR-004 §3.1]` — resolved for a specific employee if you tell it who you
are.

Built as a portfolio project to show the parts of RAG that are easy to get
subtly wrong: retrieval that misses the section that *limits* a rule,
answers that quote a superseded figure, confident extrapolation about things
the documents do not cover. The corpus was written to contain exactly those
traps, and the evaluation measures whether the system falls into them.

**Stack:** Python · LangChain 1.x / LangGraph · Claude Haiku 4.5 · Chroma ·
fastembed (`bge-base-en-v1.5`, local ONNX) · FastAPI · SQLite · one static
HTML page.

---

## Results

Retrieval, measured on 22 graded questions (36 required documents across
them), as each stage of the pipeline was added:

| Retrieval pipeline                         | Questions fully answerable | Required docs found | Context per search |
| ------------------------------------------ | -------------------------- | ------------------- | ------------------ |
| Embedding search only (k=8)                | 18 / 22                    | 32 / 36             | 3.3k chars         |
| + neighbour expansion                      | 18 / 22                    | 32 / 36             | 7.1k               |
| + reference following                      | 20 / 22                    | 34 / 36             | 8.3k               |
| + hits-only references, round-robin budget | **22 / 22**                | **36 / 36**         | 8.2k               |

Answers, graded by Claude Opus 4.6 against a written answer key
(`scripts/evaluate_answers.py`):

| Metric                               | Score       |
| ------------------------------------ | ----------- |
| Correct                              | 21 / 22     |
| Grounded in retrieved text           | 21 / 22     |
| Cited correctly                      | 22 / 22     |
| Fully passed (all three)             | 20 / 22     |
| Correctly declined (out-of-scope)    | **2 / 5**   |

The refusal score is the honest weak spot: asked about parental leave in a
country the company has no entity in, the model still tends to answer from the
global policy rather than check whether the country exists. Retrieval is clean;
refusal discipline on a small model is the open problem.

---

## Why a synthetic handbook

Real policy corpora are private, and public ones are not designed to break
RAG systems. This one is. Sixteen documents (`corpus/`) covering HR, finance,
IT, security and engineering operations for a fictional SaaS company, with
traps seeded deliberately:

- **Cross-document dependencies.** PTO accrual is in HR-004, but it depends on
  *tenure tier*, defined in HR-001. No single search finds both.
- **Superseded values.** An amendment log (POL-000) overrides figures that
  still appear in the original text — carryover is 10 days, not the 5 the
  old text says.
- **Country qualifiers.** On-call pay is USD 500 flat in the US and 12% of
  weekly base in Ireland, two sections apart. Quoting the wrong one is
  confidently wrong.
- **Near-miss vocabulary.** Salary *Zones* and travel *Tiers* are different
  systems with similar names; Singapore is in both.
- **Exceptions to the rule.** IC6 does not qualify for business class, because
  the track equivalence table maps IC7 — not IC6 — to M4.
- **Things the handbook does not cover**, where the correct answer is to say
  so: no Brazilian entity, no published salary bands, no stock price.

The evaluation set (`tests/eval_cases.py`) names which trap each question
probes and which sections a correct answer must draw on. It lives outside
`corpus/` so it can never be indexed.

---

## How it works

```
question ─► Claude (Haiku 4.5) decides to search
               │
               ▼  search_handbook("tenure tier")
          ┌──────────────────────────────────────────────┐
          │ 1. embed query, top-8 chunks from Chroma      │
          │ 2. + the chunk before and after each hit      │  neighbour expansion
          │ 3. + sections the hits cite ("see HR-001 §4") │  reference following
          └──────────────────────────────────────────────┘
               │  one text block, each chunk headed by its citation
               ▼
          Claude reads, searches again if needed, answers with citations
```

### Ingestion (`app/rag/ingest.py`)

Markdown is split on headings first (`#`, `##`, `###`), so every chunk sits
inside one subsection, then capped at 800 characters with 150 overlap for the
few oversized ones. Each chunk carries `doc_id`, `section`, `title`, and its
`position` in the document. 16 documents → 438 chunks. Embedded locally with
`bge-base-en-v1.5` (768 dims) via fastembed — no PyTorch, no API cost at
index or query time. Rebuild is wipe-and-replace:
`python -m scripts.build_index`.

### Retrieval (`app/rag/retriever.py`)

Embedding search alone ranks chunks in isolation, so it will happily return
"§8.2 Relocation Amounts" without "§8.3 Eligibility" beside it. Two expansions
add what the corpus itself says belongs alongside a hit:

- **Neighbour expansion** fetches the chunk before and after each hit by
  `(doc_id, position)`. Policy documents are written in order; the section
  that limits a rule sits next to the one that states it.
- **Reference following** regexes citations like `HR-001 §4.3` out of the
  hits and fetches those sections by label. References are collected from the
  search hits only — not from neighbours, whose §1.x boilerplate cites half
  the handbook — and resolved round-robin, so a precise `§2.3` can never be
  starved by a broad `§5` collected before it.

Neither step uses embeddings; both are metadata lookups, effectively free.
Together they took retrieval from 18/22 to 22/22 at unchanged context size.

### Agent (`app/agent.py`)

`create_agent` with one tool. The tool's docstring is prompt engineering —
it tells the model to search in the handbook's vocabulary, not the employee's,
and to search again when a result points at something unread. The system
prompt sets the citation and refusal behaviour and is kept corpus-independent.

Per-employee answers use LangGraph's `context_schema` plus a `@dynamic_prompt`
middleware: one agent, built once; who is asking arrives per invocation and
is rendered into the system prompt. Five personas in SQLite
(`app/employees.py`) sit on opposite sides of the corpus's traps, so the same
question gets a different correct answer for each.

Prompt caching is on (`cache_control` top-level): tools, system prompt and
prior turns are read back at ~10% of input price on every model call after
the first, which matters because answering one question takes at least two
calls.

### Persistence (`app/server.py`)

Conversations are LangGraph checkpoints in SQLite (`AsyncSqliteSaver`), one
thread per chat. The browser keeps only an index of thread ids in
`localStorage` and sends one message per turn; the graph loads the rest.
Reopening a chat reads the graph's own state (`GET /chats/{id}`), so there is
no second copy to drift.

Trade-offs, stated: the server is stateful (single-instance unless stores are
shared); thread ids are unguessable 122-bit UUIDs but not bound to a user; a
thread can grow without bound. Right for a demo, all three named in the code.

### Server and UI

FastAPI with SSE streaming (`search` / `token` / `done` / `error` events),
Pydantic-capped inputs, a per-IP daily token budget (300k tokens ≈ 50
questions ≈ $0.30 at Haiku prices), and a search tool that degrades to an
instruction string instead of killing the turn when Chroma fails. The UI is a
single dependency-free HTML file with a chat sidebar, persona picker, and
streaming render — model output is built into the DOM as text, never parsed
as HTML.

---

## Evaluation

Two scripts, two questions, kept separate on purpose — a right answer from the
wrong sections and a wrong answer from the right sections are different bugs.

```bash
python -m scripts.evaluate            # did the right sections come back?   (free, local)
python -m scripts.evaluate_answers    # was the answer right?  (~$0.75, judged by Opus 4.6)
```

Both measure the **actual pipeline** — search plus both expansions — not bare
similarity search. The judge sees the question, the written expected answer,
the agent's answer, and the retrieved text, and returns structured
`correct / grounded / cited` verdicts with a one-line reason, so failures are
named rather than counted.

---

## Running it

```bash
python -m venv venv && source venv/Scripts/activate     # Windows Git Bash
pip install -r requirements.txt
echo ANTHROPIC_API_KEY=sk-ant-... > .env

python -m scripts.build_index         # ~40s: embeds 438 chunks locally
python -m scripts.chat --as jdoe      # CLI; `dev` shows searches, `debug` shows chunks
uvicorn app.server:app                # http://127.0.0.1:8000
```

The persona demo in two clicks: pick **John Doe (Dublin)**, ask *"What am I
paid for being on call?"* — 12% of weekly base. New chat, **Alex Smith
(Austin)**, same question — USD 500.

---

## Layout

```
corpus/            16 handbook documents (the only thing that gets indexed)
tests/             eval_cases.py — 27 graded questions with answer key; never indexed
app/
  config.py        paths, models, budget
  rag/ingest.py    markdown → chunks → Chroma
  rag/retriever.py search + neighbours + references; the search_handbook tool
  rag/embeddings.py fastembed adapter for LangChain
  agent.py         create_agent, persona middleware, prompt caching
  employees.py     persona table (SQLite)
  server.py        FastAPI, SSE, checkpointer, budget
scripts/
  build_index.py   rebuild the index, smoke-test it
  chat.py          terminal chat with user/dev/debug output levels
  evaluate.py      retrieval eval
  evaluate_answers.py  answer eval (LLM judge)
static/index.html  the chat UI
```

---

## What I would do next

In order of expected return, each one measured against the eval before it
stays:

1. **Expand fewer hits** — neighbours for the top 3–4 only; likely holds 22/22
   at ~40% less context.
2. **Reranker before expansion** — retrieve 30, `bge-reranker-base` locally,
   keep 6, then expand; stops expansion multiplying junk.
3. **Contextual retrieval** — one Haiku call per chunk at index time writing a
   situating sentence, so caveats live inside the vector. Would have
   prevented the §8.2/§8.3 failure class outright.
4. **Hybrid BM25 + RRF** — exact-identifier queries (`HR-004 §4.2`,
   `USD 110`) where embeddings are weakest.
5. **Cap thread growth** and bind threads to an authenticated user before any
   non-demo deployment.
