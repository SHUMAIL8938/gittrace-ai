import gzip
import json
import logging
from pathlib import Path
from app.retrieval.reranker import rerank
from app.ingestion.embedder import get_model
from app.ingestion.models import Chunk
from app.ingestion.vector_store import search as vector_search
from app.retrieval.bm25_index import BM25Index
from app.retrieval.hybrid import hybrid_search

logging.basicConfig(level=logging.INFO)

CACHE_FILE = Path("chunks_cache.json.gz")


def load_chunks(cache_file: Path) -> list[Chunk]:
    if cache_file.exists():
        with gzip.open(cache_file, "rt", encoding="utf-8") as f:
            raw = json.load(f)
        chunks = [Chunk(**chunk) for chunk in raw]
        print(f"Loaded {len(chunks)} chunks from cache")
        return chunks

    print("Cache not found. Cloning, parsing and indexing...")

    import dataclasses
    from app.ingestion.cloner import clone_repo, cleanup_repo
    from app.ingestion.parser import parse_file
    from app.ingestion.embedder import embed_chunks
    from app.ingestion.vector_store import store_chunks

    repo_dir, files = clone_repo("https://github.com/tiangolo/fastapi")

    all_chunks = []
    for file_path in files:
        all_chunks.extend(
            parse_file(file_path, repo_name="fastapi", repo_dir=repo_dir)
        )

    cleanup_repo(repo_dir)

    print(f"Parsed {len(all_chunks)} chunks. Embedding...")
    embeddings = embed_chunks(all_chunks)

    print("Storing in ChromaDB...")
    store_chunks(all_chunks, embeddings, repo_name="fastapi")

    with gzip.open(cache_file, "wt", encoding="utf-8") as f:
        json.dump([dataclasses.asdict(c) for c in all_chunks], f)

    print(f"Cached {len(all_chunks)} chunks")
    return all_chunks

def print_results(
    title: str,
    results: list[dict],
) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    if not results:
        print("No results found")
        return

    for i, hit in enumerate(results, start=1):
        metadata = hit["metadata"]

        print(f"\nResult {i}")
        print("-" * 80)
        print(f"File       : {metadata['file_path']}")
        print(f"Name       : {metadata['name']}")
        print(f"Chunk Type : {metadata['chunk_type']}")
        print(f"Lines      : {metadata.get('start_line')}")

        preview = hit["text"][:300].strip()

        print("\nPreview:")
        print(preview)

        if len(hit["text"]) > 300:
            print("...")


def main() -> None:
    chunks = load_chunks(CACHE_FILE)

    print(f"Loaded {len(chunks)} chunks")

    bm25_index = BM25Index(chunks)

    model = get_model()

    query = "how does fastapi handle request validation"

    embedding = model.encode(query)

    if hasattr(embedding, "tolist"):
        embedding = embedding.tolist()

    print(f"\nQuery: {query}")

    bm25_results = bm25_index.search(
        query,
        n_results=5,
    )

    vector_results = vector_search(
        embedding,
        repo_name="fastapi",
        n_results=5,
    )

    hybrid_results = hybrid_search(
        query=query,
        query_embedding=embedding,
        repo_name="fastapi",
        bm25_index=bm25_index,
        n_results=5,
    )

    print_results(
        "BM25 RESULTS",
        bm25_results,
    )

    print_results(
        "VECTOR RESULTS",
        vector_results,
    )

    print_results(
        "HYBRID RESULTS",
        hybrid_results,
    )
    reranked_results = rerank(query, hybrid_results, top_n=5)
    print_results("RERANKED RESULTS", reranked_results)

    print("\nRerank scores:")
    for hit in reranked_results:
        print(
            f"  {hit['metadata']['name']:<40} {hit['rerank_score']}"
        )


if __name__ == "__main__":
    main()