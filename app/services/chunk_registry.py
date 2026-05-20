import json
import re
from pathlib import Path

from app.config import CHUNKS_DIR

STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "where", "what",
    "which", "when", "how", "why", "does", "are", "is", "was", "were",
    "has", "have", "had", "about", "using", "used", "show", "tell",
    "explain", "repository", "repo", "project", "code", "file", "files",
}

INTENT_KEYWORDS = {
    "readme": ["readme", "overview", "description", "installation", "usage", "features"],
    "dependencies": ["requirements", "dependencies", "packages", "libraries", "pip", "npm", "poetry", "conda", "pyproject", "package.json"],
    "run": ["run", "start", "usage", "main", "entrypoint", "command", "cli", "uvicorn", "docker compose"],
    "architecture": ["architecture", "structure", "module", "component", "service", "config", "schema", "router", "controller"],
    "api": ["api", "endpoint", "route", "request", "response", "get", "post", "put", "delete", "FastAPI", "APIRouter"],
    "frontend": ["component", "props", "state", "hook", "useState", "useEffect", "html", "css", "javascript", "typescript"],
    "data": ["data", "dataset", "source", "input", "output", "schema", "columns", "features", "csv", "json", "load"],
    "training": ["fit", ".fit", "fit(", "train", "training", "predict", "model", "Pipeline", "trainer", "epoch", "loss", "optimizer"],
    "evaluation": ["evaluate", "evaluation", "metrics", "score", "accuracy", "precision", "recall", "f1", "auc", "loss", "validation", "test"],
    "testing": ["test", "tests", "assert", "pytest", "unittest", "jest", "coverage"],
    "docker": ["Dockerfile", "docker-compose", "compose.yml", "container", "image", "ports", "volumes"],
    "ci": [".github", "workflow", "actions", "ci", "cd", "deploy", "deployment", "pipeline"],
}

INTENT_MARKERS = {
    "readme": ["readme", "documentation", "docs"],
    "dependencies": ["dependencies", "requirements", "packages", "libraries", "install", "environment"],
    "run": ["run", "start", "execute", "usage", "command", "setup"],
    "architecture": ["architecture", "structure", "modules", "components", "folders", "design"],
    "api": ["api", "endpoint", "route", "request", "response", "router"],
    "frontend": ["frontend", "ui", "interface", "component", "react", "vue", "html", "css"],
    "data": ["data", "dataset", "source", "input", "output", "csv", "json"],
    "training": ["train", "training", "fit", "model", "models", "predict", "machine learning", "ml"],
    "evaluation": ["evaluate", "evaluation", "metric", "metrics", "score", "accuracy", "f1", "loss"],
    "testing": ["test", "tests", "unit test", "pytest", "unittest", "jest"],
    "docker": ["docker", "dockerfile", "compose", "container"],
    "ci": ["github actions", "workflow", "ci", "cd", "deployment", "deploy"],
}

FILE_HINTS = {
    "readme": ["readme"],
    "requirements": ["requirements", "dependencies", "libraries", "packages"],
    "pyproject": ["pyproject"],
    "package.json": ["package.json", "npm", "node dependencies"],
    "docker": ["docker", "dockerfile", "docker compose", "compose.yml"],
    ".ipynb": ["notebook", "jupyter", "ipynb"],
    "test": ["tests", "unit tests", "pytest", "unittest", "jest"],
    "config": ["config", "configuration", "settings", ".env"],
    ".github": ["github actions", "workflow", "ci", "cd"],
}


def get_chunks_path(repo_id: str) -> Path:
    return CHUNKS_DIR / f"{repo_id}.json"


def save_repository_chunks(repo_id: str, chunks: list[dict]) -> None:
    get_chunks_path(repo_id).write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_repository_chunks(repo_id: str) -> list[dict]:
    path = get_chunks_path(repo_id)

    if not path.exists():
        return []

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def extract_query_terms(query: str) -> set[str]:
    terms = re.findall(r"[a-zA-Z_][a-zA-Z_0-9.-]+", query.lower())
    return {term for term in terms if len(term) >= 3 and term not in STOPWORDS}


def detect_query_intents(query: str) -> set[str]:
    query_lower = query.lower()
    return {
        intent
        for intent, markers in INTENT_MARKERS.items()
        if any(marker in query_lower for marker in markers)
    }


def build_keyword_list(query: str) -> list[str]:
    keywords = set(extract_query_terms(query))

    for intent in detect_query_intents(query):
        keywords.update(INTENT_KEYWORDS.get(intent, []))

    return list(keywords)


def keyword_search_chunks(repo_id: str, query: str, top_k: int = 8) -> list[dict]:
    chunks = load_repository_chunks(repo_id)
    keywords = build_keyword_list(query)

    if not chunks or not keywords:
        return []

    scored_chunks = []
    query_lower = query.lower()
    query_terms = extract_query_terms(query)

    for chunk in chunks:
        content = chunk.get("content", "")
        content_lower = content.lower()
        file_path = chunk.get("file_path", "")
        file_path_lower = file_path.lower()
        symbol_name = chunk.get("symbol_name") or ""
        symbol_name_lower = symbol_name.lower()
        chunk_type = chunk.get("chunk_type", "text")

        score = 0

        for keyword in keywords:
            keyword_lower = keyword.lower()
            score += content_lower.count(keyword_lower)

            if keyword_lower in file_path_lower:
                score += 4
            if symbol_name_lower and keyword_lower in symbol_name_lower:
                score += 6

        for term in query_terms:
            if term in file_path_lower:
                score += 5
            if symbol_name_lower and term in symbol_name_lower:
                score += 8

        if "readme" in query_lower and "readme" in file_path_lower:
            score += 20
        if "requirements" in query_lower and "requirements" in file_path_lower:
            score += 20
        if "docker" in query_lower and "docker" in file_path_lower:
            score += 20
        if ("notebook" in query_lower or "ipynb" in query_lower) and file_path_lower.endswith(".ipynb"):
            score += 20
        if chunk_type in {"function", "class"} and any(word in query_lower for word in ["function", "class", "method", "implemented", "where"]):
            score += 3

        if score > 0:
            scored_chunks.append(make_search_result(repo_id, chunk, score))

    scored_chunks.sort(key=lambda item: item["keyword_score"], reverse=True)
    return scored_chunks[:top_k]


def search_chunks_by_file_name(repo_id: str, file_name_markers: list[str], top_k: int = 5) -> list[dict]:
    results = []
    markers = [marker.lower() for marker in file_name_markers]

    for chunk in load_repository_chunks(repo_id):
        file_path_lower = chunk.get("file_path", "").lower()

        if any(marker in file_path_lower for marker in markers):
            results.append(make_search_result(repo_id, chunk, keyword_score=100))

    return results[:top_k]


def detect_file_hints(query: str) -> list[str]:
    query_lower = query.lower()
    return [
        file_marker
        for file_marker, markers in FILE_HINTS.items()
        if any(marker in query_lower for marker in markers)
    ]


def make_search_result(repo_id: str, chunk: dict, keyword_score: int) -> dict:
    return {
        "repo_id": repo_id,
        "file_path": chunk["file_path"],
        "chunk_index": chunk["chunk_index"],
        "chunk_type": chunk.get("chunk_type", "text"),
        "symbol_name": chunk.get("symbol_name") or "",
        "content": chunk.get("content", ""),
        "distance": 0.0,
        "keyword_score": keyword_score,
    }
