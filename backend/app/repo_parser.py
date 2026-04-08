import ast
import json
import zipfile
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".md": "markdown",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
}


def build_tree(paths: list[str]) -> dict:
    root: dict = {"name": "/", "type": "directory", "children": []}
    index: dict[tuple[str, ...], dict] = {(): root}
    for path in sorted(paths):
        parts = PurePosixPath(path).parts
        for depth in range(len(parts)):
            current_key = parts[: depth + 1]
            parent_key = parts[:depth]
            parent = index[parent_key]
            if current_key not in index:
                node = {
                    "name": parts[depth],
                    "type": "file" if depth == len(parts) - 1 else "directory",
                }
                if node["type"] == "directory":
                    node["children"] = []
                parent["children"].append(node)
                index[current_key] = node
    return root


def extract_python_symbols(content: str) -> list[dict]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []

    symbols: list[dict] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            symbols.append(
                {
                    "type": "function",
                    "name": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "args": [arg.arg for arg in node.args.args],
                }
            )
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append(
                {
                    "type": "async_function",
                    "name": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "args": [arg.arg for arg in node.args.args],
                }
            )
        elif isinstance(node, ast.ClassDef):
            methods = [child.name for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))]
            symbols.append(
                {
                    "type": "class",
                    "name": node.name,
                    "docstring": ast.get_docstring(node) or "",
                    "methods": methods,
                }
            )
    return symbols


def parse_repository_from_directory(root_path: Path, preview_chars: int = 2500) -> dict:
    files: list[dict] = []
    for file_path in root_path.rglob("*"):
        if not file_path.is_file():
            continue
        rel_path = file_path.relative_to(root_path).as_posix()
        if "__MACOSX" in rel_path or rel_path.endswith("/"):
            continue
        ext = file_path.suffix.lower()
        language = SUPPORTED_EXTENSIONS.get(ext, "text")
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="latin-1", errors="ignore")
        symbols = extract_python_symbols(content) if language == "python" else []
        files.append(
            {
                "path": rel_path,
                "language": language,
                "symbols": symbols,
                "content_preview": content[:preview_chars],
            }
        )

    tree = build_tree([item["path"] for item in files])
    metadata = {
        "file_count": len(files),
        "python_file_count": sum(1 for item in files if item["language"] == "python"),
        "languages": sorted({item["language"] for item in files}),
    }
    return {"tree": tree, "files": files, "metadata": metadata}


def parse_repository_from_zip(zip_path: Path, preview_chars: int = 2500) -> dict:
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(temp_path)

        directories = [item for item in temp_path.iterdir() if item.is_dir()]
        root_path = directories[0] if len(directories) == 1 else temp_path
        return parse_repository_from_directory(root_path, preview_chars=preview_chars)


def serialize_json(data: dict | list) -> str:
    return json.dumps(data, ensure_ascii=True)
