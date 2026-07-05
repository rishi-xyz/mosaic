import os

from slack_sdk import WebClient


def get_slack_client() -> WebClient | None:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if token:
        return WebClient(token=token)
    return None
