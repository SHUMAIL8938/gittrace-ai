import logging
import re
from rank_bm25 import BM25Okapi
from app.ingestion.models import Chunk

logger = logging.getLogger(__name__)

def _tokenize(text:str)->list[str]:
    text=text.lower()
    tokens=re.findall(r"[a-zA-Z0-9_]+",text)
    return tokens

class BM25Index:
    def __init__(self,chunks:list[Chunk])->None:
        if not chunks:
            raise ValueError("cannot build index from empty list")
        self._chunks=chunks
        tokenized=[_tokenize(chunk.text) for chunk in chunks]
        self._index= BM25Okapi(tokenized)
        logger.info("Build index over %d chunks",len(chunks))
    def search(
            self,
            query:str,
            n_results:int=10,
    )->list[dict]:
        tokens=_tokenize(query)
        if not tokens:
            logger.warning("BM25 recieved empty query-> tokenization")
            return []
        scores=self._index.get_scores(tokens)

        scored=sorted(
            enumerate(scores),
            key=lambda x:x[1],
            reverse=True
        )[:n_results]

        results=[]
        for idx, score in scored:
            if score <= 0:
                continue
            results.append({
                "text": self._chunks[idx].text,
                "metadata": {
                    "file_path": self._chunks[idx].file_path,
                    "language": self._chunks[idx].language,
                    "chunk_type": self._chunks[idx].chunk_type,
                    "name": self._chunks[idx].name,
                    "start_line": self._chunks[idx].start_line,
                    "end_line": self._chunks[idx].end_line,
                    "repo_name": self._chunks[idx].repo_name,
                },
                "score": round(float(score), 4),
            })

        return results
