import logging
from sentence_transformers import SentenceTransformer
from app.ingestion.models import Chunk
logger=logging.getLogger(__name__)
MODEL_NAME="all-MiniLM-L6-v2"
_model=None
def get_model()->SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        _model=SentenceTransformer(MODEL_NAME)
    return _model
def embed_chunks(chunks:list[Chunk])->list[list[float]]:
    model=get_model()
    texts=[chunk.text for chunk in chunks]
    logger.info(f"Embedding {len(texts)} chunks in batches...")
    embeddings=model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True
    )
    return embeddings.tolist()