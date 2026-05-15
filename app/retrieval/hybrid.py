import logging
from app.ingestion.models import Chunk
from app.ingestion.vector_store import search as vector_search
from app.retrieval.bm25_index import BM25Index
from collections import defaultdict

logger = logging.getLogger(__name__)



def hybrid_search(
        query:str,
        query_embedding:list[float],
        repo_name:str,
        bm25_index:BM25Index,
        n_results:int=10,
) -> list[dict]:
    bm25_results=bm25_index.search(query,n_results=n_results)
    vector_results = vector_search(query_embedding,repo_name,n_results=n_results)

    logger.info(
        "BM25 returned %d results , vector search returned %d results",len(bm25_results),len(vector_results),
    )
    