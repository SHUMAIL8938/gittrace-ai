from app.ingestion.cloner import clone_repo, cleanup_repo
repo_dir, files = clone_repo("https://github.com/SHUMAIL8938/gittrace-ai")
print(f"Cloned to: {repo_dir}")
print(f"Total files found: {len(files)}")
print("\nFirst 10 files:")
for f in files[:10]:
    print(" ", f)
cleanup_repo(repo_dir)
print("\nCleaned up.")