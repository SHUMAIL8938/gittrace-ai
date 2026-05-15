import logging
from app.ingestion.models import Chunk
from app.ingestion.vector_store import search as vector_search
from app.retrieval.bm25_index import BM25Index
from collections import defaultdict

logger = logging.getLogger(__name__)

def _make_chunk_key(result: dict) -> str:
    metadata = result["metadata"]

    return (
        f"{metadata['file_path']}::"
        f"{metadata['name']}::"
        f"{metadata['start_line']}"
    )

def reciprocal_rank_fusion(
        bm25_results:list[dict],
        vector_results:list[dict],
        k:int=60,
)-> list[dict]:
    scores:dict[str,float]=defaultdict(float)
    chunks:dict[str,dict]={}

    for rank, result in enumerate(bm25_results):
        key=_make_chunk_key(result)
        scores[key]+=1/(k+rank+1)

        if  key not in chunks:
            chunks[key]=result

    for rank, result in enumerate(vector_results):
        key=_make_chunk_key(result)
        scores[key]+=1/(k+rank+1)

        if  key not in chunks:
            chunks[key]=result
    ranked =sorted(scores.items(),key=lambda x:x[1], reverse=True)

    return [chunks[key] for key,_ in ranked]
    
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

    merged=reciprocal_rank_fusion(bm25_results,vector_results)
    return merged[:n_results]