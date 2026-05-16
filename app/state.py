import logging
import uuid
from app.retrieval.bm25_index import BM25Index
from app.ingestion.models import Chunk
import chromadb

from app.ingestion.vector_store import (
    list_indexed_repos,
    get_all_chunks,
    _create_chroma_client,
)
logger=logging.getLogger(__name__)

class JobStatus:
    PENDING="pending"
    CLONING="cloning"
    PARSING="parsing"
    EMBEDDING="embedding"
    STORING="storing"
    READY="ready"
    FAILED="failed"

class AppState:
    def __init__(self)->None :
        self.job:dict[str,dict]={}
        self.bm25_indexes:dict[str,BM25Index]={}
        self.indexing_repos:set[str]=set()
        self.chroma_client: chromadb.ClientAPI | None=None

    def get_chroma_client(self)->chromadb.ClientAPI:
        try:
            if self.chroma_client:
                self.chroma_client.heartbeat()
                return self.chroma_client
        except Exception:
            logger.warning("Existing Chroma client is not healthy, creating a new one")
            self.chroma_client=None
        
        self.chroma_client=_create_chroma_client()
        return self.chroma_client
    
    async def initialize(self)->None:
        logger.info("Initializing app state")

        repos=list_indexed_repos()
        logger.info("found %d indexed repos",len(repos))

        for repo_name in repos:
            try:
                await self._build_bm25(repo_name)
            except Exception as e:
                logger.error(
                    "Failed to rebuild BM25 for %s : %s",repo_name,e
                )
            logger.info("App state initialized")