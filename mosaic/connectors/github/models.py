from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawCommit:
    sha: str
    message: str
    author_login: str
    author_name: str
    author_email: str
    committed_at: datetime
    diff_patch: str
    files_changed: list[str]
    repo_name: str


@dataclass
class RawPullRequest:
    number: int
    title: str
    body: str
    state: str
    author_login: str
    created_at: datetime
    merged_at: Optional[datetime]
    closed_at: Optional[datetime]
    base_branch: str
    head_branch: str
    commits: list[RawCommit]
    reviewers: list[str]
    repo_name: str
    linked_issue_numbers: list[int] = field(default_factory=list)


@dataclass
class RawReview:
    id: int
    pr_number: int
    reviewer_login: str
    state: str
    body: str
    submitted_at: datetime
    repo_name: str


@dataclass
class RawIssue:
    number: int
    title: str
    body: str
    state: str
    author_login: str
    created_at: datetime
    closed_at: Optional[datetime]
    labels: list[str]
    repo_name: str


@dataclass
class RawRepoData:
    owner: str
    name: str
    commits: list[RawCommit]
    pull_requests: list[RawPullRequest]
    issues: list[RawIssue]
    reviews: list[RawReview]
