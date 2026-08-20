from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

CORPUS_DIR = Path(BASE_DIR/"corpus")
CHROMA_DIR = Path(BASE_DIR/"data"/"chroma")
COLLECTION_NAME = "handbook"

# Demo employee profiles. Rebuilt from the seed in app/employees.py, so it is
# disposable like the Chroma index — none of it is real personal data.
EMPLOYEE_DB = BASE_DIR / "data" / "employees.db"

# Conversation persistence (LangGraph checkpoints, one thread per chat). Unlike
# the two databases above this one is real user state — deleting it deletes
# everyone's chat history, so it is not rebuild-on-boot.
CHATS_DB = BASE_DIR / "data" / "chats.db"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
# 8 rather than 5: many handbook questions need chunks from two or three
# documents at once, and the model filters what it reads. A missed chunk is
# fatal, an extra one costs ~80 tokens.
TOP_K = 8
# Neighbour expansion (the chunk before and after a hit) applies to the top
# hits only. Hit 1 is almost always on topic, so its neighbours are worth
# reading; hit 8 is often a loose match, and its neighbours are padding.
NEIGHBOUR_HITS = 4
CHAT_MODEL = "claude-haiku-4-5"

# Grading model for scripts/evaluate_answers.py. Deliberately stronger than
# CHAT_MODEL — a judge no smarter than what it grades tends to agree with it.
# Never used at request time, so this costs per eval run, not per user.
JUDGE_MODEL = "claude-opus-4-6"

# Per-IP daily ceiling for the public demo, in model tokens (input + output,
# cached included). 300k is roughly 30-40 questions — plenty to try the demo,
# not enough to make farming the endpoint worthwhile. Worst case per IP per day
# at Haiku prices is a few tenths of a dollar.
DAILY_TOKEN_BUDGET = 300_000

# Turns (user messages) one chat may hold before the server asks for a new
# one. Every turn re-sends the whole thread to the model, so an unbounded chat
# is a cost that grows quadratically with its length. 30 turns is far more
# than a demo conversation needs and bounds the worst case at ~40k tokens of
# history, which is also roughly where Haiku's answers start to drift.
MAX_TURNS_PER_CHAT = 30

# 768 dimensions. Roughly 5x the parameters of all-MiniLM-L6-v2 (384 dims) and
# noticeably better at retrieval, still small enough to run on CPU via ONNX.
EMBED_MODEL = "BAAI/bge-base-en-v1.5"

# fastembed defaults to the system temp folder, which Windows is free to clear.
# Pin it next to the other model caches so a rebuild never re-downloads.
EMBED_CACHE_DIR = Path.home() / ".cache" / "fastembed"

