import logging
from sentence_transformers import CrossEncoder
 
logger=logging.getLogger(__name__)

MODEL_NAME="BAAI/bge-reranker-based"
_model :CrossEncoder|None=None

class RerankerError(Exception):
    """raised wnen reranking fails"""

def get_reranker()-> CrossEncoder:
    global _model
    if _model is None:
        logger.info("Loading reranking model %s",MODEL_NAME)
        
        try:
            _model=CrossEncoder(MODEL_NAME)
        except Exception as e:
            raise RerankerError(f"failed to load reranker {e}") from e
    return _model

def rerank(
    query:str,
    results:list[dict],
    top_n:int=5,

) -> list[dict]:
    if not results:
        logger.warning("rerank called with empty results")
        return []
    
    reranker=get_reranker()

    pairs=[
        (query,hit["text"])
        for hit in results
    ]
    
    try:
        scores= reranker.predict(pairs)
    except Exception as e:
        raise RerankerError(
            f"reranking failed {e}"
        ) from e
    
    scored_results=[]

    for hit,score in zip(results,scores):
        enriched={
            **hit,
            "rerank_score":float(score),
        }
        scored_results.append(enriched)
    
    reranked=sorted(
        scored_results,
        key=lambda x:x["rerank_score"],
        reverse=True
    )

    logger.info(
        "Reranked %d results, returning top %d",
        len(results),
        top_n,
    )

    return reranked[:top_n]