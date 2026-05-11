import json
import gzip
from pathlib import Path

from app.ingestion.embedder import embed_chunks, get_model
from app.ingestion.models import Chunk
from app.ingestion.vector_store import store_chunks, search

CACHE_FILE = Path("chunks_cache.json.gz")

if not CACHE_FILE.exists():
    raise FileNotFoundError(
        f"Cache file not found: {CACHE_FILE.resolve()}"
    )

with gzip.open(CACHE_FILE, "rt", encoding="utf-8") as file:
    raw = json.load(file)

chunks = [Chunk(**c) for c in raw]

# chunks = chunks[:500]
print(f"Loaded {len(chunks)} chunks")

embeddings = embed_chunks(chunks)

print(f"Embedded {len(embeddings)} chunks")

store_chunks(
    chunks,
    embeddings,
    repo_name="fastapi",
    overwrite=True
)

print("Stored in ChromaDB")
model = get_model()
query = "what is fast api?"
query_vector = model.encode(query).tolist()

results = search(
    query_embedding=query_vector,
    repo_name="fastapi",
    n_results=3,
)

print(f"\nQuery: '{query}'")
print("-" * 50)

for i, hit in enumerate(results, start=1):
    print(f"\nResult {i} — score: {hit['score']}")

    print(f"File : {hit['metadata']['file_path']}")
    print(f"Name : {hit['metadata']['name']}")
    print(f"Type : {hit['metadata']['chunk_type']}")

    print(f"Preview:\n{hit['text'][:200]}")