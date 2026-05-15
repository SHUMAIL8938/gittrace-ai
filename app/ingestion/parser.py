import logging
from pathlib import Path
from tree_sitter_languages import get_parser
from app.ingestion.models import Chunk

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".cpp": "cpp",
    ".c": "c",
}

NODE_TYPES = {
    "python": {
        "function_definition": "function",
        "class_definition": "class",
    },
    "javascript": {
        "function_declaration": "function",
        "class_declaration": "class",
    },
    "typescript": {
        "function_declaration": "function",
        "class_declaration": "class",
    },
    "go": {
        "function_declaration": "function",
        "type_declaration": "class",
    },
    "rust": {
        "function_definition": "function",
        "struct_definition": "class",
    },
    "java": {
        "method_declaration": "function",
        "class_declaration": "class",
    },
}

MAX_CHUNK_LINES = 100


class ParserError(Exception):
    """Raised when a file cannot be parsed."""


def _relative_path(file_path: str, repo_dir: str) -> str:
    """Convert absolute path to repo-relative path."""
    if not repo_dir:
        return file_path
    try:
        return Path(file_path).relative_to(repo_dir).as_posix()
    except ValueError:
        return file_path


def _split_large_chunk(chunk: Chunk) -> list[Chunk]:
    """
    Split chunks that exceed MAX_CHUNK_LINES into smaller pieces.
    Preserves the function/class name on the first piece only.
    """
    lines = chunk.text.splitlines()

    if len(lines) <= MAX_CHUNK_LINES:
        return [chunk]

    pieces = []
    for i, start in enumerate(range(0, len(lines), MAX_CHUNK_LINES)):
        piece_lines = lines[start:start + MAX_CHUNK_LINES]
        piece_text = "\n".join(piece_lines)

        try:
            pieces.append(Chunk(
                text=piece_text,
                file_path=chunk.file_path,
                language=chunk.language,
                start_line=chunk.start_line + start,
                end_line=chunk.start_line + start + len(piece_lines) - 1,
                chunk_type=chunk.chunk_type,
                name=chunk.name if i == 0 else f"{chunk.name}__part{i + 1}",
                repo_name=chunk.repo_name,
            ))
        except ValueError as e:
            logger.debug("Skipping empty piece of %s: %s", chunk.name, e)

    return pieces


def _walk_iterative(
    root_node,
    source_bytes: bytes,
    file_path: str,
    language: str,
    repo_name: str,
) -> list[Chunk]:
    chunks = []
    valid_types = NODE_TYPES.get(language, {})
    stack = [root_node]

    while stack:
        node = stack.pop()

        if node.type in valid_types:
            try:
                text = (
                    source_bytes[node.start_byte:node.end_byte]
                    .decode("utf-8", errors="ignore")
                    .strip()
                )

                name = ""
                for child in node.children:
                    if child.type == "identifier":
                        name = child.text.decode("utf-8", errors="ignore")
                        break

                chunk = Chunk(
                    text=text,
                    file_path=file_path,
                    language=language,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    chunk_type=valid_types[node.type],
                    name=name,
                    repo_name=repo_name,
                )

                chunks.extend(_split_large_chunk(chunk))

            except ValueError as e:
                logger.debug("Skipping invalid chunk in %s: %s", file_path, e)

        stack.extend(node.children)

    return chunks


def parse_file(
    file_path: str,
    repo_name: str,
    repo_dir: str = "",
) -> list[Chunk]:

    path = Path(file_path)
    ext = path.suffix.lower()
    language = LANGUAGE_MAP.get(ext)
    stored_path = _relative_path(file_path, repo_dir)

    try:
        source_bytes = path.read_bytes()
    except OSError as e:
        logger.warning("Could not read %s: %s", file_path, e)
        return []

    if language:
        try:
            parser = get_parser(language)
            tree = parser.parse(source_bytes)
            chunks = _walk_iterative(
                tree.root_node, source_bytes, stored_path, language, repo_name
            )
            logger.debug("Parsed %d chunks from %s", len(chunks), path.name)
            return chunks
        except Exception as e:
            logger.warning("Could not parse %s: %s", file_path, e)
            return []

    try:
        return [Chunk(
            text=source_bytes.decode("utf-8", errors="ignore"),
            file_path=stored_path,
            language=ext.lstrip("."),
            start_line=1,
            end_line=source_bytes.count(b"\n") + 1,
            chunk_type="file",
            name=path.name,
            repo_name=repo_name,
        )]
    except ValueError as e:
        logger.debug("Skipping empty file %s: %s", file_path, e)
        return []