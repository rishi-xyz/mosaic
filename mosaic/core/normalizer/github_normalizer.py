from mosaic.connectors.github.models import RawRepoData, RawCommit, RawPullRequest, RawIssue, RawReview
from mosaic.core.store import save_patch

from .schemas import (
    NormalizedCommit,
    NormalizedPullRequest,
    NormalizedIssue,
    NormalizedReview,
    NormalizedFile,
    NormalizedAuthor,
)


def _make_author_id(login: str) -> str:
    return f"github:user:{login}"


def _make_commit_id(repo: str, sha: str) -> str:
    return f"github:commit:{repo}:{sha}"


def _make_pr_id(repo: str, number: int) -> str:
    return f"github:pr:{repo}:{number}"


def _make_issue_id(repo: str, number: int) -> str:
    return f"github:issue:{repo}:{number}"


def _make_review_id(repo: str, review_id: int) -> str:
    return f"github:review:{repo}:{review_id}"


def _make_file_id(repo: str, path: str) -> str:
    return f"github:file:{repo}:{path}"


def normalize_commit(raw: RawCommit, pr_number: int | None = None) -> NormalizedCommit:
    commit_id = _make_commit_id(raw.repo_name, raw.sha)

    patch_path = ""
    if raw.diff_patch:
        patch_path = save_patch(raw.repo_name, raw.sha, raw.diff_patch)

    return NormalizedCommit(
        source_id=commit_id,
        title=raw.message.split("\n")[0],
        body=raw.message,
        created_at=raw.committed_at,
        author_id=_make_author_id(raw.author_login),
        repo_name=raw.repo_name,
        metadata={
            "sha": raw.sha,
            "author_name": raw.author_name,
            "author_email": raw.author_email,
            "files_changed": raw.files_changed,
            "patch_path": patch_path,
        },
        sha=raw.sha,
        message=raw.message,
        diff_summary=raw.message,
        files_changed=raw.files_changed,
        pr_number=pr_number,
        linked_entity_ids=[_make_author_id(raw.author_login)] + [_make_file_id(raw.repo_name, f) for f in raw.files_changed],
    )


def normalize_pull_request(raw: RawPullRequest) -> NormalizedPullRequest:
    pr_id = _make_pr_id(raw.repo_name, raw.number)
    commit_ids = [_make_commit_id(raw.repo_name, c.sha) for c in raw.commits]
    return NormalizedPullRequest(
        source_id=pr_id,
        title=raw.title,
        body=raw.body,
        created_at=raw.created_at,
        author_id=_make_author_id(raw.author_login),
        repo_name=raw.repo_name,
        metadata={
            "state": raw.state,
            "base_branch": raw.base_branch,
            "head_branch": raw.head_branch,
            "reviewers": raw.reviewers,
            "linked_issue_numbers": raw.linked_issue_numbers,
        },
        number=raw.number,
        state=raw.state,
        merged_at=raw.merged_at,
        base_branch=raw.base_branch,
        head_branch=raw.head_branch,
        reviewers=raw.reviewers,
        commit_ids=commit_ids,
        linked_issue_numbers=raw.linked_issue_numbers,
        linked_entity_ids=[_make_author_id(raw.author_login)] + commit_ids + [_make_issue_id(raw.repo_name, n) for n in raw.linked_issue_numbers],
    )


def normalize_issue(raw: RawIssue) -> NormalizedIssue:
    issue_id = _make_issue_id(raw.repo_name, raw.number)
    return NormalizedIssue(
        source_id=issue_id,
        title=raw.title,
        body=raw.body,
        created_at=raw.created_at,
        author_id=_make_author_id(raw.author_login),
        repo_name=raw.repo_name,
        metadata={
            "state": raw.state,
            "labels": raw.labels,
        },
        number=raw.number,
        state=raw.state,
        closed_at=raw.closed_at,
        labels=raw.labels,
        linked_entity_ids=[_make_author_id(raw.author_login)],
    )


def normalize_review(raw: RawReview) -> NormalizedReview:
    review_id = _make_review_id(raw.repo_name, raw.id)
    pr_id = _make_pr_id(raw.repo_name, raw.pr_number)
    return NormalizedReview(
        source_id=review_id,
        title=f"Review on PR #{raw.pr_number} by {raw.reviewer_login}",
        body=raw.body,
        created_at=raw.submitted_at,
        author_id=_make_author_id(raw.reviewer_login),
        repo_name=raw.repo_name,
        metadata={
            "state": raw.state,
            "pr_number": raw.pr_number,
        },
        pr_number=raw.pr_number,
        state=raw.state,
        linked_entity_ids=[_make_author_id(raw.reviewer_login), pr_id],
    )


def normalize_entities(raw: RawRepoData) -> dict[str, list]:
    authors: dict[str, NormalizedAuthor] = {}
    files: dict[str, NormalizedFile] = {}
    commits: list[NormalizedCommit] = []
    prs: list[NormalizedPullRequest] = []
    issues: list[NormalizedIssue] = []
    reviews: list[NormalizedReview] = []

    for raw_pr in raw.pull_requests:
        for raw_commit in raw_pr.commits:
            commit = normalize_commit(raw_commit, pr_number=raw_pr.number)
            commits.append(commit)

            if raw_commit.author_login not in authors:
                authors[raw_commit.author_login] = NormalizedAuthor(
                    source_id=_make_author_id(raw_commit.author_login),
                    title=raw_commit.author_login,
                    repo_name=raw.repo_name,
                    login=raw_commit.author_login,
                )

            for fpath in raw_commit.files_changed:
                fid = _make_file_id(raw.repo_name, fpath)
                if fpath not in files:
                    files[fpath] = NormalizedFile(
                        source_id=fid,
                        title=fpath,
                        repo_name=raw.repo_name,
                        path=fpath,
                    )

        pr = normalize_pull_request(raw_pr)
        prs.append(pr)

    for raw_commit in raw.commits:
        if not any(c.source_id == _make_commit_id(raw.repo_name, raw_commit.sha) for c in commits):
            commit = normalize_commit(raw_commit)
            commits.append(commit)

            if raw_commit.author_login not in authors:
                authors[raw_commit.author_login] = NormalizedAuthor(
                    source_id=_make_author_id(raw_commit.author_login),
                    title=raw_commit.author_login,
                    repo_name=raw.repo_name,
                    login=raw_commit.author_login,
                )

            for fpath in raw_commit.files_changed:
                fid = _make_file_id(raw.repo_name, fpath)
                if fpath not in files:
                    files[fpath] = NormalizedFile(
                        source_id=fid,
                        title=fpath,
                        repo_name=raw.repo_name,
                        path=fpath,
                    )

    for raw_issue in raw.issues:
        issue = normalize_issue(raw_issue)
        issues.append(issue)

        if raw_issue.author_login not in authors:
            authors[raw_issue.author_login] = NormalizedAuthor(
                source_id=_make_author_id(raw_issue.author_login),
                title=raw_issue.author_login,
                repo_name=raw.repo_name,
                login=raw_issue.author_login,
            )

        for pr in prs:
            if raw_issue.number in pr.linked_issue_numbers:
                issue.linked_pr_number = pr.number
                issue.linked_entity_ids.append(pr.source_id)
                pr.linked_entity_ids.append(issue.source_id)

    for raw_review in raw.reviews:
        review = normalize_review(raw_review)
        reviews.append(review)

        if raw_review.reviewer_login not in authors:
            authors[raw_review.reviewer_login] = NormalizedAuthor(
                source_id=_make_author_id(raw_review.reviewer_login),
                title=raw_review.reviewer_login,
                repo_name=raw.repo_name,
                login=raw_review.reviewer_login,
            )

    return {
        "authors": list(authors.values()),
        "files": list(files.values()),
        "commits": commits,
        "pull_requests": prs,
        "issues": issues,
        "reviews": reviews,
    }
