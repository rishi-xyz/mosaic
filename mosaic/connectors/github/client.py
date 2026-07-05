import os
from github import Github, Auth
from github.Repository import Repository


def get_github_client(config: dict | None = None) -> Github:
    """Get GitHub client with optional config dict.
    
    Args:
        config: Optional config dict with 'GITHUB_TOKEN' key.
                If not provided, falls back to os.environ.
    """
    token = None
    if config:
        token = config.get("GITHUB_TOKEN")
    if not token:
        token = os.environ.get("GITHUB_TOKEN")
    
    if token:
        return Github(auth=Auth.Token(token))
    return Github()


def get_repo(client: Github, repo_full: str) -> Repository:
    return client.get_repo(repo_full)
