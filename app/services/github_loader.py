import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

from git import GitCommandError, Repo


def normalize_repo_url(repo_url: str) -> str:
    return repo_url.strip().rstrip("/")


def get_repo_info(repo_url: str) -> tuple[str, str, str]:
    normalized_url = normalize_repo_url(repo_url)
    parsed = urlparse(normalized_url)
    path_parts = parsed.path.strip("/").split("/")

    if parsed.netloc not in {"github.com", "www.github.com"} or len(path_parts) < 2:
        raise ValueError("Please provide a valid GitHub repository URL.")

    owner = path_parts[0].lower()
    repo_name = path_parts[1].removesuffix(".git")
    safe_repo_name = re.sub(r"[^a-z0-9_.-]", "-", repo_name.lower())
    repo_id = f"{owner}__{safe_repo_name}"

    return owner, repo_name, repo_id


def clone_or_update_repository(repo_url: str, target_dir: Path) -> dict:
    normalized_url = normalize_repo_url(repo_url)
    _, repo_name, repo_id = get_repo_info(normalized_url)
    repo_path = target_dir / repo_id

    if repo_path.exists():
        try:
            repo = Repo(repo_path)
            repo.remotes.origin.pull()
            action = "updated"
        except GitCommandError:
            action = "existing"
        except Exception:
            shutil.rmtree(repo_path)
            Repo.clone_from(normalized_url, repo_path)
            action = "recloned"
    else:
        Repo.clone_from(normalized_url, repo_path)
        action = "cloned"

    return {
        "repo_url": normalized_url,
        "repo_id": repo_id,
        "repo_name": repo_name,
        "repo_path": repo_path,
        "action": action,
    }
