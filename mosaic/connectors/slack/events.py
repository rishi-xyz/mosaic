import json
import os
from pathlib import Path
from typing import Optional

from slack_sdk import WebClient

from .models import RawSlackChannel, RawSlackData, RawSlackMessage


_FIXTURE_PATH = Path("mosaic/fixtures/slack/messages.json")


def _load_fixture() -> RawSlackData | None:
    if not _FIXTURE_PATH.exists():
        return None
    data = json.loads(_FIXTURE_PATH.read_text())
    channel = RawSlackChannel(**data["channel"])
    messages = [RawSlackMessage(**m) for m in data["messages"]]
    return RawSlackData(channel=channel, messages=messages)


def fetch_channel_info(client: WebClient, channel_id: str) -> RawSlackChannel:
    resp = client.conversations_info(channel=channel_id)
    c = resp["channel"]
    return RawSlackChannel(
        id=c["id"],
        name=c["name"],
        topic=c.get("topic", {}).get("value", ""),
        members=[m for m in c.get("members", [])],
    )


def fetch_messages(
    client: WebClient, channel_id: str, limit: int = 100
) -> list[RawSlackMessage]:
    raw_messages: list[RawSlackMessage] = []
    resp = client.conversations_history(channel=channel_id, limit=limit)
    channel_name = ""
    try:
        channel_name = fetch_channel_info(client, channel_id).name
    except Exception:
        pass

    for msg in resp.get("messages", []):
        if msg.get("subtype") and msg["subtype"] != "thread_reply":
            continue

        thread_ts = msg.get("thread_ts")
        replies: list[str] = []
        if thread_ts:
            try:
                thread_resp = client.conversations_replies(
                    channel=channel_id, ts=thread_ts, limit=50
                )
                replies = [
                    r["text"]
                    for r in thread_resp.get("messages", [])
                    if r.get("ts") != thread_ts
                ]
            except Exception:
                pass

        permalink = ""
        try:
            permalink_resp = client.chat_getPermalink(
                channel=channel_id, message_ts=msg["ts"]
            )
            permalink = permalink_resp.get("permalink", "")
        except Exception:
            pass

        raw_messages.append(
            RawSlackMessage(
                ts=msg["ts"],
                channel=channel_id,
                channel_name=channel_name,
                user=msg.get("user", "unknown"),
                text=msg.get("text", ""),
                thread_ts=thread_ts,
                replies=replies,
                permalink=permalink,
            )
        )

    return raw_messages


def fetch_channels(client: WebClient) -> list[RawSlackChannel]:
    channels: list[RawSlackChannel] = []
    cursor = None

    while True:
        kwargs: dict = {"types": "public_channel,private_channel", "limit": 200}
        if cursor:
            kwargs["cursor"] = cursor
        resp = client.conversations_list(**kwargs)
        for c in resp.get("channels", []):
            channels.append(
                RawSlackChannel(
                    id=c["id"],
                    name=c["name"],
                    topic=c.get("topic", {}).get("value", ""),
                    members=[m for m in c.get("members", [])],
                )
            )
        cursor = resp.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break

    return channels


def fetch_all(
    client: Optional[WebClient] = None,
    channel_names: Optional[list[str]] = None,
    max_messages: int = 100,
) -> list[RawSlackData]:
    use_fixtures = (
        os.environ.get("SLACK_USE_FIXTURES", "").lower() in ("true", "1", "yes")
    )

    if use_fixtures or client is None:
        result = _load_fixture()
        if result:
            return [result]
        return []

    if channel_names:
        all_channels = fetch_channels(client)
        targets = [c for c in all_channels if c.name in channel_names]
    else:
        targets = fetch_channels(client)

    results: list[RawSlackData] = []
    for channel in targets:
        messages = fetch_messages(client, channel.id, limit=max_messages)
        if messages:
            results.append(RawSlackData(channel=channel, messages=messages))

    return results
