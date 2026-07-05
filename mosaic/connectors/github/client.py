import os
from github import Github, Auth
from github.Repository import Repository


def get_github_client() -> Github:
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return Github(auth=Auth.Token(token))
    return Github()


def get_repo(client: Github, repo_full: str) -> Repository:
    return client.get_repo(repo_full)
