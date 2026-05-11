import logging
from dataclasses import dataclass
logger = logging.getLogger(__name__)

@dataclass
class Chunk:
    text: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str
    name: str
    repo_name: str

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError(f"Chunk text cannot be empty: {self.file_path}")
        if self.chunk_type not in {"function", "class", "file"}:
            raise ValueError(f"Invalid chunk_type: {self.chunk_type}")
        if self.start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {self.start_line}")

    @property
    def size(self) -> int:
        """Number of characters in this chunk."""
        return len(self.text)

    @property
    def short_path(self) -> str:
        """Just filename, not full path. Useful for citations."""
        from pathlib import Path
        return Path(self.file_path).name