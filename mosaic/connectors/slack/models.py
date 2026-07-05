from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawSlackMessage:
    ts: str
    channel: str
    channel_name: str
    user: str
    text: str
    thread_ts: Optional[str] = None
    replies: list[str] = field(default_factory=list)
    permalink: str = ""
    created_at: datetime | None = None


@dataclass
class RawSlackChannel:
    id: str
    name: str
    topic: str = ""
    members: list[str] = field(default_factory=list)


@dataclass
class RawSlackData:
    channel: RawSlackChannel
    messages: list[RawSlackMessage]
