import json
from pathlib import Path

from app.utils.file_filters import should_process_file


def read_notebook_file(file_path: Path) -> str:
    notebook = json.loads(file_path.read_text(encoding="utf-8"))
    parts = []

    for index, cell in enumerate(notebook.get("cells", [])):
        cell_type = cell.get("cell_type")
        source = cell.get("source", "")
        source_text = "".join(source) if isinstance(source, list) else str(source)
        source_text = source_text.strip()

        if not source_text:
            continue

        if cell_type == "markdown":
            parts.append(f"# Markdown cell {index}\n{source_text}")
        elif cell_type == "code":
            parts.append(f"# Code cell {index}\n```python\n{source_text}\n```")

    return "\n\n".join(parts)


def read_text_file(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def read_repository_files(repo_path: Path) -> list[dict]:
    files_data = []

    for file_path in repo_path.rglob("*"):
        if not file_path.is_file() or not should_process_file(file_path):
            continue

        try:
            if file_path.suffix.lower() == ".ipynb":
                content = read_notebook_file(file_path)
            else:
                content = read_text_file(file_path)
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            continue

        if not content.strip():
            continue

        files_data.append(
            {
                "path": str(file_path.relative_to(repo_path)),
                "extension": file_path.suffix.lower(),
                "content": content,
            }
        )

    return files_data
