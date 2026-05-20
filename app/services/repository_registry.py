import json

from app.config import DATA_DIR

REGISTRY_PATH = DATA_DIR / "repositories.json"
DEFAULT_REGISTRY = {"active_repo_id": None, "repositories": {}}


def load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return DEFAULT_REGISTRY.copy()

    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_REGISTRY.copy()


def save_registry(registry: dict) -> None:
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def register_repository(repo_info: dict) -> None:
    registry = load_registry()
    repo_id = repo_info["repo_id"]

    registry["repositories"][repo_id] = {
        "repo_id": repo_id,
        "repo_name": repo_info["repo_name"],
        "repo_url": repo_info["repo_url"],
        "repo_path": str(repo_info["repo_path"]),
    }
    registry["active_repo_id"] = repo_id

    save_registry(registry)


def list_repositories() -> list[dict]:
    return list(load_registry()["repositories"].values())


def get_active_repo_id() -> str | None:
    return load_registry().get("active_repo_id")


def set_active_repo_id(repo_id: str) -> None:
    registry = load_registry()

    if repo_id not in registry["repositories"]:
        raise ValueError(f"Repository with repo_id '{repo_id}' is not registered.")

    registry["active_repo_id"] = repo_id
    save_registry(registry)


def resolve_repo_id(repo_id: str | None) -> str:
    if repo_id:
        return repo_id

    active_repo_id = get_active_repo_id()

    if not active_repo_id:
        raise ValueError("No repository selected. Please index a repository first.")

    return active_repo_id
