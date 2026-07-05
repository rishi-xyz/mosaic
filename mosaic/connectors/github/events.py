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


def _to_raw_commit(gh_commit, repo_name: str) -> RawCommit:
    return RawCommit(
        sha=gh_commit.sha,
        message=gh_commit.commit.message,
        author_login=gh_commit.author.login if gh_commit.author else "unknown",
        author_name=gh_commit.commit.author.name,
        author_email=gh_commit.commit.author.email,
        committed_at=gh_commit.commit.author.date,
        diff_patch=_get_diff_patch(gh_commit),
        files_changed=[f.filename for f in (gh_commit.files or [])],
        repo_name=repo_name,
    )


def fetch_commits(
    repo: Repository,
    since: datetime | None = None,
    max_count: int = 100,
) -> list[RawCommit]:
    kwargs = {}
    if since:
        kwargs["since"] = since

    raw_commits = []
    for i, gh_commit in enumerate(repo.get_commits(**kwargs)):
        if i >= max_count:
            break
        raw_commits.append(_to_raw_commit(gh_commit, repo.full_name))
    return raw_commits


def fetch_pull_requests(
    repo: Repository,
    state: str = "all",
    max_count: int = 50,
) -> tuple[list[RawPullRequest], list[GhPullRequest]]:
    raw_prs: list[RawPullRequest] = []
    gh_prs: list[GhPullRequest] = []

    for i, gh_pr in enumerate(repo.get_pulls(state=state, sort="updated", direction="desc")):
        if i >= max_count:
            break
        gh_prs.append(gh_pr)
        pr_commits = [_to_raw_commit(c, repo.full_name) for c in gh_pr.get_commits()]

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

    return raw_prs, gh_prs


def fetch_issues(
    repo: Repository,
    state: str = "all",
    max_count: int = 100,
) -> list[RawIssue]:
    raw_issues = []
    for i, gh_issue in enumerate(repo.get_issues(state=state, sort="updated", direction="desc")):
        if i >= max_count:
            break
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


def fetch_reviews(
    gh_prs: list[GhPullRequest],
    repo_name: str,
) -> list[RawReview]:
    raw_reviews = []
    for gh_pr in gh_prs:
        for r in gh_pr.get_reviews():
            if not r.user:
                continue
            raw_reviews.append(
                RawReview(
                    id=r.id,
                    pr_number=gh_pr.number,
                    reviewer_login=r.user.login,
                    state=r.state,
                    body=r.body or "",
                    submitted_at=r.submitted_at,
                    repo_name=repo_name,
                )
            )
    return raw_reviews


def fetch_all(
    repo: Repository,
    since: datetime | None = None,
    max_prs: int = 50,
    max_commits: int = 100,
    max_issues: int = 100,
) -> RawRepoData:
    commits = fetch_commits(repo, since, max_commits)
    pull_requests, gh_prs = fetch_pull_requests(repo, max_count=max_prs)
    issues = fetch_issues(repo, max_count=max_issues)
    reviews = fetch_reviews(gh_prs, repo.full_name)
    return RawRepoData(
        owner=repo.owner.login,
        name=repo.name,
        commits=commits,
        pull_requests=pull_requests,
        issues=issues,
        reviews=reviews,
    )
