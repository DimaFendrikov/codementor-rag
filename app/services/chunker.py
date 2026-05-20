import ast
import re


def chunk_text_by_lines(text: str, max_chunk_size: int = 1600, overlap_lines: int = 4) -> list[str]:
    if not text.strip():
        return []

    chunks = []
    current_lines = []
    current_size = 0

    for line in text.splitlines():
        line_size = len(line) + 1

        if current_lines and current_size + line_size > max_chunk_size:
            chunks.append("\n".join(current_lines).strip())
            current_lines = current_lines[-overlap_lines:]
            current_size = sum(len(item) + 1 for item in current_lines)

        current_lines.append(line)
        current_size += line_size

    if current_lines:
        chunks.append("\n".join(current_lines).strip())

    return [chunk for chunk in chunks if chunk]


def chunk_python_file(text: str) -> list[dict]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return make_text_chunks(text, "text")

    lines = text.splitlines()
    chunks = []
    used_lines = set()

    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        start_line = node.lineno
        end_line = getattr(node, "end_lineno", node.lineno)
        source = "\n".join(lines[start_line - 1:end_line]).strip()
        chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"

        chunks.append(
            {
                "content": source,
                "chunk_type": chunk_type,
                "symbol_name": node.name,
            }
        )
        used_lines.update(range(start_line, end_line + 1))

    module_text = "\n".join(
        line for line_number, line in enumerate(lines, start=1) if line_number not in used_lines
    ).strip()

    module_chunks = make_text_chunks(module_text, "module") if module_text else []
    return module_chunks + chunks if chunks or module_chunks else make_text_chunks(text, "text")


def chunk_notebook_text(text: str) -> list[dict]:
    pattern = r"(?=^# (?:Markdown|Code) cell \d+)"
    raw_cells = re.split(pattern, text, flags=re.MULTILINE)
    chunks = []

    for raw_cell in raw_cells:
        raw_cell = raw_cell.strip()
        if not raw_cell:
            continue

        first_line = raw_cell.splitlines()[0]
        match = re.match(r"# (Markdown|Code) cell (\d+)", first_line)
        cell_kind = match.group(1).lower() if match else "cell"
        cell_number = match.group(2) if match else str(len(chunks))

        if len(raw_cell) <= 2200:
            chunks.append(
                {
                    "content": raw_cell,
                    "chunk_type": f"notebook_{cell_kind}_cell",
                    "symbol_name": f"{cell_kind}_cell_{cell_number}",
                }
            )
            continue

        for part_index, part in enumerate(chunk_text_by_lines(raw_cell, 1800, 3)):
            chunks.append(
                {
                    "content": part,
                    "chunk_type": f"notebook_{cell_kind}_cell",
                    "symbol_name": f"{cell_kind}_cell_{cell_number}_part_{part_index}",
                }
            )

    return chunks


def make_text_chunks(text: str, chunk_type: str) -> list[dict]:
    return [
        {
            "content": chunk,
            "chunk_type": chunk_type,
            "symbol_name": "",
        }
        for chunk in chunk_text_by_lines(text)
    ]


def chunk_repository_files(files_data: list[dict]) -> list[dict]:
    all_chunks = []

    for file_data in files_data:
        extension = file_data.get("extension", "")
        content = file_data["content"]

        if extension == ".py":
            chunks = chunk_python_file(content)
        elif extension == ".ipynb":
            chunks = chunk_notebook_text(content)
        else:
            chunks = make_text_chunks(content, "text")

        for index, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "file_path": file_data["path"],
                    "chunk_index": index,
                    "content": chunk["content"],
                    "chunk_type": chunk.get("chunk_type", "text"),
                    "symbol_name": chunk.get("symbol_name") or "",
                }
            )

    return all_chunks
