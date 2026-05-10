import os
import tempfile
import shutil
import git
import logging

logger = logging.getLogger(__name__)

IGNORE_DIRS = {
    ".git",
    ".github",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "target",
    "vendor",
    ".idea",
    ".vscode",
    "eggs",
    ".eggs",
    "docs",
    "site",
    "test",
    "tests",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "env",
}

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".r",
    ".sh",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".md",
    ".sql",
    ".html",
    ".css",
}

MAX_FILE_BYTES = 100_000
class ClonerError(Exception):
    """Raised when cloning fails."""
    pass

def clone_repo(github_url: str) -> tuple[str, list[str]]:
    repo_dir = tempfile.mkdtemp(prefix="rag_")
    try:
        logger.info("Cloning %s -> %s", github_url, repo_dir)
        git.Repo.clone_from(github_url, repo_dir, depth=1)
    except git.GitCommandError as e:
        shutil.rmtree(repo_dir, ignore_errors=True)
        raise ClonerError(f"Failed to clone {github_url}: {e}") from e
    file_paths = _scan_files(repo_dir)
    logger.info("Found %d indexable files", len(file_paths))
    return repo_dir, file_paths

def _scan_files(repo_dir: str) -> list[str]:
    file_paths = []
    for root, dirnames, filenames in os.walk(repo_dir):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for filename in filenames:
            filepath = os.path.join(root, filename)
            _, ext = os.path.splitext(filename)
            if ext.lower() not in ALLOWED_EXTENSIONS:
                continue
            try:
                if os.path.getsize(filepath) > MAX_FILE_BYTES:
                    logger.debug("Skipping large file: %s", filepath)
                    continue
            except OSError:
                logger.debug("Skipping unreadable file: %s", filepath)
                continue
            file_paths.append(filepath)
    return file_paths

def cleanup_repo(repo_dir: str) -> None:
    logger.info("Cleaning up %s", repo_dir)
    shutil.rmtree(repo_dir, ignore_errors=True)
