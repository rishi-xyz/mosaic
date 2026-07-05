import os
from pathlib import Path


_DEFAULT_STORE_DIR = Path("data/patches")


def _ensure_store_dir(store_dir: Path = _DEFAULT_STORE_DIR) -> Path:
    store_dir.mkdir(parents=True, exist_ok=True)
    return store_dir


def _patch_path(repo_name: str, sha: str, store_dir: Path = _DEFAULT_STORE_DIR) -> Path:
    return store_dir / repo_name / f"{sha}.patch"


def save_patch(repo_name: str, sha: str, diff_patch: str, store_dir: Path = _DEFAULT_STORE_DIR) -> str:
    path = _patch_path(repo_name, sha, store_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(diff_patch)
    return str(path)


def read_patch(patch_path: str) -> str:
    path = Path(patch_path)
    if path.exists():
        return path.read_text()
    return ""
