import logging
from pathlib import Path
from tree_sitter_languages import get_language, get_parser
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


def extract_chunks_from_ast(
    source_bytes: bytes,
    file_path: str,
    language: str,
    repo_name: str,
) -> list[Chunk]:
    chunks = []
    try:
        parser = get_parser(language)
        tree = parser.parse(source_bytes)
    except Exception as e:
        logger.warning(f"Could not parse{file_path}:{e}")
        return chunks

    def walk(node):
        valid_types = NODE_TYPES.get(language, [])
        if node.type in valid_types:
            text = source_bytes[node.start_byte : node.end_byte].decode(
                "utf-8", errors="ignore"
            )
            name = ""
            for child in node.children:
                if child.type == "identifier":
                    name = child.text.decode("utf-8", errors="ignore")
                    break
            chunks.append(
                Chunk(
                    text=text,
                    file_path=file_path,
                    language=language,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    chunk_type="function"
                    if node.type == "function_definition"
                    else "class",
                    name=name,
                    repo_name=repo_name,
                )
            )
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return chunks


def parse_file(
    file_path: str,
    repo_name: str,
) -> list[Chunk]:

    path = Path(file_path)
    ext = path.suffix.lower()
    language = LANGUAGE_MAP.get(ext)

    try:
        source_bytes = path.read_bytes()
    except Exception as e:
        logger.warning(f"Could not read {file_path}: {e}")
        return []

    if language:
        return extract_chunks_from_ast(source_bytes, file_path, language, repo_name)
    return [
        Chunk(
            text=source_bytes.decode("utf-8", errors="ignore"),
            file_path=file_path,
            language=ext.lstrip("."),
            start_line=1,
            end_line=source_bytes.count(b"\n") + 1,
            chunk_type="file",
            name=path.name,
            repo_name=repo_name,
        )
    ]
