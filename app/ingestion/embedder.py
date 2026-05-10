import logging
from sentence_transformers import SentenceTransformer
from app.ingestion.models import Chunk

logger = logging.getLogger(__name__)
MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None

class EmbeddingError(Exception):
    """Raised when embedding fails"""

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", MODEL_NAME)
        try:
            _model = SentenceTransformer(MODEL_NAME)
        except Exception as e:
            raise EmbeddingError(f"failed to load model {MODEL_NAME}: {e}") from e
    return _model


def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    if not chunks:
        logger.warning("embed_chunks called with empty list")
        return []
    model = get_model()
    texts = [chunk.text for chunk in chunks]
    logger.info("Embedding %d chunks...", len(texts))
    try:
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
        )
    except Exception as e:
        raise EmbeddingError(f"Encoding failed: {e}") from e
    return embeddings.tolist()
