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

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
# 8 rather than 5: many handbook questions need chunks from two or three
# documents at once, and the model filters what it reads. A missed chunk is
# fatal, an extra one costs ~80 tokens.
TOP_K = 8
CHAT_MODEL = "claude-haiku-4-5"

# Grading model for scripts/evaluate_answers.py. Deliberately stronger than
# CHAT_MODEL — a judge no smarter than what it grades tends to agree with it.
# Never used at request time, so this costs per eval run, not per user.
JUDGE_MODEL = "claude-opus-4-6"

# 768 dimensions. Roughly 5x the parameters of all-MiniLM-L6-v2 (384 dims) and
# noticeably better at retrieval, still small enough to run on CPU via ONNX.
EMBED_MODEL = "BAAI/bge-base-en-v1.5"

# fastembed defaults to the system temp folder, which Windows is free to clear.
# Pin it next to the other model caches so a rebuild never re-downloads.
EMBED_CACHE_DIR = Path.home() / ".cache" / "fastembed"

