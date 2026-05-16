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

logger = logging.getLogger(__name__)

class JobStatus:
    PENDING = "pending"
    CLONING = "cloning"
    PARSING = "parsing"
    EMBEDDING = "embedding"
    STORING = "storing"
    READY = "ready"
    FAILED = "failed"

class AppState:
    def __init__(self) -> None:
        self.job: dict[str, dict] = {}
        self.bm25_indexes: dict[str, BM25Index] = {}
        self.indexing_repos: set[str] = set()
        self.chroma_client: chromadb.ClientAPI | None = None

    def get_chroma_client(self) -> chromadb.ClientAPI:
        try:
            if self.chroma_client:
                self.chroma_client.heartbeat()
                return self.chroma_client
        except Exception:
            logger.warning("Existing Chroma client is not healthy, creating a new one")
            self.chroma_client = None

        self.chroma_client = _create_chroma_client()
        return self.chroma_client

    async def initialize(self) -> None:
        logger.info("Initializing app state")

        repos = list_indexed_repos()
        logger.info("found %d indexed repos", len(repos))

        for repo_name in repos:
            try:
                await self._build_bm25(repo_name)
            except Exception as e:
                logger.error("Failed to rebuild BM25 for %s : %s", repo_name, e)
            logger.info("App state initialized")

    async def _build_bm25(self, repo_name: str) -> None:
        """fetch chunk from chroma and build bm25 over it"""
        logger.info("Building BM25 index for '%s", repo_name)

        raw_chunks = get_all_chunks(repo_name)

        if not raw_chunks:
            logger.warning("No chunks found for '%s' skipping BM25 over it", repo_name)
            return
        chunks = [
            Chunk(
                text=c["text"],
                file_path=c["metadata"]["file_path"],
                language=c["metadata"]["language"],
                chunk_type=c["metadata"]["chunk_type"],
                name=c["metadata"]["name"],
                start_line=c["metadata"]["start_line"],
                end_line=c["metadata"]["end_line"],
                repo_name=c["metadata"]["repo_name"],
            )
            for c in raw_chunks
        ]
        self.bm25_indexes[repo_name]=BM25Index(chunks)
        logger.info(
            "BM25 ready for '%s' - chunks",repo_name,len(chunks)
        )
