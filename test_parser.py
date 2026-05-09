from app.ingestion.cloner import clone_repo, cleanup_repo
from app.ingestion.parser import parse_file

repo_dir, files = clone_repo("https://github.com/tiangolo/fastapi")

all_chunks = []
for file_path in files:
    chunks = parse_file(file_path, repo_name="fastapi")
    all_chunks.extend(chunks)
python_chunks = [
    c for c in all_chunks
    if c.language == "python" and c.chunk_type == "function"
]
print(f"Total chunks: {len(all_chunks)}")
print(f"Python function chunks: {len(python_chunks)}")
print("\n--- Sample chunk ---")
sample = python_chunks[0]
print(f"Name     : {sample.name}")
print(f"Type     : {sample.chunk_type}")
print(f"Language : {sample.language}")
print(f"File     : {sample.file_path}")
print(f"Lines    : {sample.start_line} → {sample.end_line}")
print(f"Text preview:\n{sample.text[:200]}")

cleanup_repo(repo_dir)