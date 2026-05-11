import logging
import re
import chromadb
from chromadb.config import Settings
from app.ingestion.models import Chunk
import hashlib

logger=logging.getLogger(__name__)

CHROMA_PATH="chroma_db"
MAX_BATCH_SIZE=500

class VectorStoreError(Exception):
    """Raised when vector storing fails"""

def _get_client()->chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(anonymized_telemetry=False),
    )
def _sanitize_name(name:str)->str:
    sanitized=re.sub(r"[^a-zA-Z0-9-]","-",name)
    return sanitized[:63]

def _make_chunk_id(chunk: Chunk) -> str:
    raw = f"{chunk.file_path}::{chunk.name}::{chunk.start_line}"
    return hashlib.md5(raw.encode()).hexdigest()

def store_chunks(
        chunks:list[Chunk],
        embeddings:list[list[float]],
        repo_name:str,
)->None:
    if not chunks:
        logger.warning("store_chunks called with empty list")
        return
    if len(chunks)!=len(embeddings):
        raise VectorStoreError(
            f"chunks and embeddings length mismatch:{len(chunks)} vs {len(embeddings)}"
        )
    client=_get_client()
    collection_name =_sanitize_name(repo_name)

    collection=client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space":"cosine"},
    )

    ids,texts,metadatas=[],[],[]

    for chunk, embedding in zip(chunks,embeddings):
        ids.append(_make_chunk_id(chunk))
        texts.append(chunk.text)
        metadatas.append({
            "file_path":chunk.file_path,
            "language":chunk.language,
            "chunk_type":chunk.chunk_type,
            "name":chunk.name,
            "start_line":chunk.start_line,
            "end_line":chunk.end_line,
            "repo_name":chunk.repo_name,
        })
    for i in range(0,len(chunks),MAX_BATCH_SIZE):
            batch_ids=ids[i:i+MAX_BATCH_SIZE]
            batch_texts=texts[i:i+MAX_BATCH_SIZE]
            batch_embeddings=embeddings[i:i+MAX_BATCH_SIZE]
            batch_metadatas=metadatas[i:i+MAX_BATCH_SIZE]
            try:
                collection.upsert(
                    ids=batch_ids,
                    documents=batch_texts,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas
                    )
            except Exception as e:
                raise VectorStoreError(f"failed to store vectors: {e}") from e
            
            logger.info("stored batch %d-%d",i,i+len(batch_ids))
        
    logger.info("stored %d chunks into collection '%s'",len(chunks),collection_name)