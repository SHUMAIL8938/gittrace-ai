import json
import gzip
import dataclasses
from pathlib import Path

from app.ingestion.cloner import clone_repo, cleanup_repo
from app.ingestion.parser import parse_file
from app.ingestion.embedder import embed_chunks
from app.ingestion.models import Chunk

CACHE_FILE = Path("chunks_cache.json.gz")


def get_chunks():

    if CACHE_FILE.exists():
        print("Loading chunks from cache...")

        with gzip.open(CACHE_FILE, "rt", encoding="utf-8") as f:
            raw = json.load(f)

        return [Chunk(**c) for c in raw]

    print("Cloning and parsing (first time only)...")

    repo_dir, files = clone_repo(
        "https://github.com/tiangolo/fastapi"
    )

    all_chunks = []

    for file_path in files:
        all_chunks.extend(
            parse_file(file_path, repo_name="fastapi")
        )

    cleanup_repo(repo_dir)

    with gzip.open(CACHE_FILE, "wt", encoding="utf-8") as f:
        json.dump(
            [dataclasses.asdict(c) for c in all_chunks],
            f
        )

    print(f"Cached {len(all_chunks)} chunks")

    return all_chunks


chunks = get_chunks()


embeddings = embed_chunks(chunks)

print(f"Chunks embedded: {len(embeddings)}")
print(f"Vector size: {len(embeddings[0])}")
print(f"First 5 numbers: {embeddings[0][:5]}")