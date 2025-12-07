import base64
import os
from datetime import datetime, timezone

import base64
import os
from datetime import datetime, timezone

import requests


class ZoomIntegrationError(Exception):
    """Raised when Zoom API interactions fail or are misconfigured."""


def _get_env_setting(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ZoomIntegrationError(f"Missing Zoom configuration: {key}")
    return value


def _get_zoom_access_token() -> str:
    """Exchange a Server-to-Server OAuth access token."""

    client_id = _get_env_setting("ZOOM_CLIENT_ID")
    client_secret = _get_env_setting("ZOOM_CLIENT_SECRET")
    account_id = _get_env_setting("ZOOM_ACCOUNT_ID")

    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    params = {"grant_type": "account_credentials", "account_id": account_id}
    headers = {"Authorization": f"Basic {b64_auth}"}

    try:
        resp = requests.post(
            "https://zoom.us/oauth/token", headers=headers, params=params, timeout=10
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ZoomIntegrationError("Failed to obtain Zoom access token") from exc

    token = resp.json().get("access_token")
    if not token:
        raise ZoomIntegrationError("Zoom access token missing in response")
    return token


def create_zoom_meeting(
    *,
    start_time: datetime,
    duration_minutes: int,
    topic: str | None = None,
    user_id: str = "me",
) -> dict:
    """Create a Zoom meeting and return key details."""

    access_token = _get_zoom_access_token()
    start_time_utc = start_time.astimezone(timezone.utc)

    url = f"https://api.zoom.us/v2/users/{user_id}/meetings"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body = {
        "topic": topic or "Lesson Meeting",
        "type": 2,
        "start_time": start_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration": max(1, int(duration_minutes)),
        "timezone": "UTC",
        "settings": {
            "join_before_host": False,
            "waiting_room": True,
            "auto_recording": "cloud",
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ZoomIntegrationError("Failed to create Zoom meeting") from exc

    meeting = resp.json()
    for key in ("id", "join_url", "start_url"):
        if key not in meeting:
            raise ZoomIntegrationError("Zoom meeting response missing required fields")

    return {
        "id": meeting["id"],
        "join_url": meeting["join_url"],
        "start_url": meeting["start_url"],
    }
