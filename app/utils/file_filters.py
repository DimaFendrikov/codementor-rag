from pathlib import Path

ALLOWED_EXTENSIONS = {
    ".py", ".ipynb", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".cpp", ".c", ".h", ".hpp", ".cs", ".go", ".rs",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".html", ".css", ".sql", ".sh", ".bat", ".ps1",
}

IGNORED_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", "venv", ".venv", "env", "dist", "build",
    ".idea", ".vscode", ".ipynb_checkpoints",
}

MAX_FILE_SIZE_BYTES = 1_000_000


def should_process_file(file_path: Path) -> bool:
    if any(part in IGNORED_DIRS for part in file_path.parts):
        return False

    if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False

    try:
        return file_path.stat().st_size <= MAX_FILE_SIZE_BYTES
    except OSError:
        return False
