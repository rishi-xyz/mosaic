from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EntityType(str, Enum):
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    REVIEW = "review"
    FILE = "file"
    AUTHOR = "author"
    DECISION = "decision"
    SLACK_MESSAGE = "slack_message"


class Source(str, Enum):
    GITHUB = "github"
    SLACK = "slack"


@dataclass
class NormalizedEntity:
    entity_type: EntityType
    source: Source
    source_id: str
    title: str
    body: str
    created_at: datetime
    author_id: str
    repo_name: str
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)


@dataclass
class NormalizedCommit:
    entity_type: EntityType = EntityType.COMMIT
    source: Source = Source.GITHUB
    source_id: str = ""
    title: str = ""
    body: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    repo_name: str = ""
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)
    sha: str = ""
    message: str = ""
    diff_summary: str = ""
    files_changed: list[str] = field(default_factory=list)
    pr_number: int | None = None


@dataclass
class NormalizedPullRequest:
    entity_type: EntityType = EntityType.PULL_REQUEST
    source: Source = Source.GITHUB
    source_id: str = ""
    title: str = ""
    body: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    repo_name: str = ""
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)
    number: int = 0
    state: str = ""
    merged_at: datetime | None = None
    base_branch: str = ""
    head_branch: str = ""
    reviewers: list[str] = field(default_factory=list)
    commit_ids: list[str] = field(default_factory=list)
    linked_issue_numbers: list[int] = field(default_factory=list)


@dataclass
class NormalizedIssue:
    entity_type: EntityType = EntityType.ISSUE
    source: Source = Source.GITHUB
    source_id: str = ""
    title: str = ""
    body: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    repo_name: str = ""
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)
    number: int = 0
    state: str = ""
    closed_at: datetime | None = None
    labels: list[str] = field(default_factory=list)
    linked_pr_number: int | None = None


@dataclass
class NormalizedReview:
    entity_type: EntityType = EntityType.REVIEW
    source: Source = Source.GITHUB
    source_id: str = ""
    title: str = ""
    body: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    repo_name: str = ""
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)
    pr_number: int = 0
    state: str = ""


@dataclass
class NormalizedFile:
    entity_type: EntityType = EntityType.FILE
    source: Source = Source.GITHUB
    source_id: str = ""
    title: str = ""
    body: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    repo_name: str = ""
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)
    path: str = ""


@dataclass
class NormalizedAuthor:
    entity_type: EntityType = EntityType.AUTHOR
    source: Source = Source.GITHUB
    source_id: str = ""
    title: str = ""
    body: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    repo_name: str = ""
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)
    login: str = ""


@dataclass
class NormalizedDecision:
    entity_type: EntityType = EntityType.DECISION
    source: Source = Source.GITHUB
    source_id: str = ""
    title: str = ""
    body: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    repo_name: str = ""
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)
    pr_number: int = 0
    issue_number: int = 0
    description: str = ""


@dataclass
class NormalizedSlackMessage:
    entity_type: EntityType = EntityType.SLACK_MESSAGE
    source: Source = Source.SLACK
    source_id: str = ""
    title: str = ""
    body: str = ""
    created_at: datetime | None = None
    author_id: str = ""
    repo_name: str = ""
    metadata: dict = field(default_factory=dict)
    linked_entity_ids: list[str] = field(default_factory=list)
    channel: str = ""
    channel_name: str = ""
    thread_ts: str = ""
    is_thread_reply: bool = False
    replies: list[str] = field(default_factory=list)
    permalink: str = ""
