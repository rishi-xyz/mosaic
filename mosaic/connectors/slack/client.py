import os

from slack_sdk import WebClient


def get_slack_client(config: dict | None = None) -> WebClient | None:
    """Get Slack client with optional config dict.
    
    Args:
        config: Optional config dict with 'SLACK_BOT_TOKEN' key.
                If not provided, falls back to os.environ.
    """
    token = None
    if config:
        token = config.get("SLACK_BOT_TOKEN")
    if not token:
        token = os.environ.get("SLACK_BOT_TOKEN")
    
    if token:
        return WebClient(token=token)
    return None
