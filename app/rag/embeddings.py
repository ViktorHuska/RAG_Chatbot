"""Local embedding model, exposed through LangChain's `Embeddings` interface.

fastembed runs the model through ONNX Runtime, so there is no PyTorch and no
GPU requirement — the whole dependency is a few megabytes on top of the
onnxruntime that chromadb already installs. That keeps the deployed app small
enough for a free hosting tier, which was the point of embedding locally.

Swap the model by changing `EMBED_MODEL` in config and rebuilding the index.
Changing it *without* rebuilding silently breaks search: query vectors from one
model mean nothing against document vectors from another.
"""

from fastembed import TextEmbedding
from langchain_core.embeddings import Embeddings

from app.config import EMBED_CACHE_DIR, EMBED_MODEL


class LocalEmbeddings(Embeddings):
    """Embeds text locally via fastembed. Default model is bge-base-en-v1.5."""

    def __init__(self, model_name: str = EMBED_MODEL) -> None:
        # Downloads the model on first use, then reads from cache. Held on the
        # instance because loading costs a second or two — build one of these
        # per process, not one per call.
        self._model = TextEmbedding(
            model_name=model_name,
            cache_dir=str(EMBED_CACHE_DIR),
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents, preserving input order."""
        # `embed` returns a generator of numpy arrays, so it has to be iterated
        # rather than indexed. `.tolist()` turns each row into plain Python
        # floats, keeping numpy out of everything downstream.
        return [vector.tolist() for vector in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        """Embed a single search query."""
        # Deliberately NOT delegating to embed_documents. Many retrieval models
        # treat queries and documents differently — E5 prefixes them, BGE has an
        # optional query instruction — and fastembed routes that through
        # `query_embed`. For bge-base-en-v1.5 this happens to be identical to
        # `embed`, but going through the right entry point means swapping in an
        # asymmetric model stays a one-line config change.
        return list(self._model.query_embed([text]))[0].tolist()