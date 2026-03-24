"""Embedding service using fastembed.

Wraps the fastembed TextEmbedding model for batch embedding of text chunks.
Model is downloaded once and cached in ~/.imagin-docs-mcp/models/.
"""

import logging

from src.config import EMBEDDING_MODEL, MODELS_DIR
from src.utils.paths import ensure_dir


logger = logging.getLogger(__name__)


class Embedder:
    """Lazy-loaded embedding model wrapper."""

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self._model_name = model_name
        self._model: object | None = None

    def _load_model(self) -> None:
        """Load the fastembed model on first use."""
        if self._model is not None:
            return

        from fastembed import TextEmbedding

        cache_dir = ensure_dir(MODELS_DIR)
        logger.info("Loading embedding model %s (cache: %s)", self._model_name, cache_dir)
        self._model = TextEmbedding(
            model_name=self._model_name,
            cache_dir=str(cache_dir),
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts into vectors.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (one per input text).
        """
        if not texts:
            return []

        self._load_model()

        embeddings = list(self._model.embed(texts))  # type: ignore[union-attr]
        return [e.tolist() for e in embeddings]
