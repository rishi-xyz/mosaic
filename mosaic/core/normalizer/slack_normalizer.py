from mosaic.connectors.slack.models import RawSlackData, RawSlackMessage
from .schemas import NormalizedAuthor, NormalizedSlackMessage


def _make_author_id(user: str) -> str:
    return f"slack:user:{user}"


def _make_message_id(channel: str, ts: str) -> str:
    return f"slack:message:{channel}:{ts}"


def normalize_slack_message(
    raw: RawSlackMessage,
) -> NormalizedSlackMessage:
    return NormalizedSlackMessage(
        source_id=_make_message_id(raw.channel, raw.ts),
        title=raw.text.split("\n")[0],
        body=raw.text,
        created_at=raw.created_at,
        author_id=_make_author_id(raw.user),
        repo_name=raw.channel_name,
        metadata={
            "channel": raw.channel,
            "channel_name": raw.channel_name,
            "thread_ts": raw.thread_ts or "",
            "is_thread_reply": raw.thread_ts is not None,
        },
        channel=raw.channel,
        channel_name=raw.channel_name,
        thread_ts=raw.thread_ts or "",
        is_thread_reply=raw.thread_ts is not None,
        replies=raw.replies,
        permalink=raw.permalink,
        linked_entity_ids=[_make_author_id(raw.user)],
    )


def normalize_slack_data(data: RawSlackData) -> dict[str, list]:
    authors: dict[str, NormalizedAuthor] = {}
    messages: list[NormalizedSlackMessage] = []

    for raw_msg in data.messages:
        msg = normalize_slack_message(raw_msg)
        messages.append(msg)

        user_key = raw_msg.user
        if user_key not in authors:
            authors[user_key] = NormalizedAuthor(
                source_id=_make_author_id(user_key),
                title=user_key,
                repo_name=data.channel.name,
                login=user_key,
            )

    return {
        "authors": list(authors.values()),
        "slack_messages": messages,
    }
