import re
from datetime import datetime, timezone

from github.Repository import Repository
from github.PullRequest import PullRequest as GhPullRequest

from .models import (
    RawCommit,
    RawPullRequest,
    RawReview,
    RawIssue,
    RawRepoData,
)


def _extract_linked_issue_numbers(body: str) -> list[int]:
    if not body:
        return []
    pattern = r"(?:closes|fixes|resolves|closed|fixed|resolved)\s+#(\d+)"
    matches = re.findall(pattern, body, re.IGNORECASE)
    return [int(m) for m in matches]


def _get_diff_patch(commit) -> str:
    if commit.files:
        patches = []
        for f in commit.files:
            patch = getattr(f, "patch", None)
            if patch:
                patches.append(f"--- a/{f.filename}\n+++ b/{f.filename}\n{patch}")
        return "\n".join(patches)
    return ""


def fetch_commits(repo: Repository, since: datetime | None = None) -> list[RawCommit]:
    kwargs = {}
    if since:
        kwargs["since"] = since

    raw_commits = []
    for gh_commit in repo.get_commits(**kwargs):
        raw_commits.append(
            RawCommit(
                sha=gh_commit.sha,
                message=gh_commit.commit.message,
                author_login=gh_commit.author.login if gh_commit.author else "unknown",
                author_name=gh_commit.commit.author.name,
                author_email=gh_commit.commit.author.email,
                committed_at=gh_commit.commit.author.date,
                diff_patch=_get_diff_patch(gh_commit),
                files_changed=[f.filename for f in (gh_commit.files or [])],
                repo_name=repo.full_name,
            )
        )
    return raw_commits


def fetch_pull_requests(repo: Repository, state: str = "all") -> list[RawPullRequest]:
    raw_prs = []
    for gh_pr in repo.get_pulls(state=state, sort="updated", direction="desc"):
        pr_commits = []
        for gh_commit in gh_pr.get_commits():
            pr_commits.append(
                RawCommit(
                    sha=gh_commit.sha,
                    message=gh_commit.commit.message,
                    author_login=gh_commit.author.login if gh_commit.author else "unknown",
                    author_name=gh_commit.commit.author.name,
                    author_email=gh_commit.commit.author.email,
                    committed_at=gh_commit.commit.author.date,
                    diff_patch=_get_diff_patch(gh_commit),
                    files_changed=[f.filename for f in (gh_commit.files or [])],
                    repo_name=repo.full_name,
                )
            )

        raw_prs.append(
            RawPullRequest(
                number=gh_pr.number,
                title=gh_pr.title,
                body=gh_pr.body or "",
                state=gh_pr.state,
                author_login=gh_pr.user.login,
                created_at=gh_pr.created_at,
                merged_at=gh_pr.merged_at,
                closed_at=gh_pr.closed_at,
                base_branch=gh_pr.base.ref,
                head_branch=gh_pr.head.ref,
                commits=pr_commits,
                reviewers=[r.user.login for r in gh_pr.get_reviews() if r.user],
                linked_issue_numbers=_extract_linked_issue_numbers(gh_pr.body),
                repo_name=repo.full_name,
            )
        )
    return raw_prs


def fetch_issues(repo: Repository, state: str = "all") -> list[RawIssue]:
    raw_issues = []
    for gh_issue in repo.get_issues(state=state, sort="updated", direction="desc"):
        if gh_issue.pull_request:
            continue
        raw_issues.append(
            RawIssue(
                number=gh_issue.number,
                title=gh_issue.title,
                body=gh_issue.body or "",
                state=gh_issue.state,
                author_login=gh_issue.user.login,
                created_at=gh_issue.created_at,
                closed_at=gh_issue.closed_at,
                labels=[l.name for l in gh_issue.labels],
                repo_name=repo.full_name,
            )
        )
    return raw_issues


def fetch_reviews(repo: Repository, pull_requests: list[RawPullRequest]) -> list[RawReview]:
    gh_prs = {pr.number: pr for pr in repo.get_pulls(state="all")}
    raw_reviews = []
    for raw_pr in pull_requests:
        gh_pr = gh_prs.get(raw_pr.number)
        if not gh_pr:
            continue
        for r in gh_pr.get_reviews():
            if not r.user:
                continue
            raw_reviews.append(
                RawReview(
                    id=r.id,
                    pr_number=raw_pr.number,
                    reviewer_login=r.user.login,
                    state=r.state,
                    body=r.body or "",
                    submitted_at=r.submitted_at,
                    repo_name=repo.full_name,
                )
            )
    return raw_reviews


def fetch_all(repo: Repository, since: datetime | None = None) -> RawRepoData:
    commits = fetch_commits(repo, since)
    pull_requests = fetch_pull_requests(repo)
    issues = fetch_issues(repo)
    reviews = fetch_reviews(repo, pull_requests)
    return RawRepoData(
        owner=repo.owner.login,
        name=repo.name,
        commits=commits,
        pull_requests=pull_requests,
        issues=issues,
        reviews=reviews,
    )
