import base64
import os
from datetime import datetime, timezone
from urllib.parse import quote

import requests

from .logger import get_logger


logger = get_logger(__name__)


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
        logger.error("Failed to obtain Zoom access token: %s", exc)
        raise ZoomIntegrationError("Failed to obtain Zoom access token") from exc

    token = resp.json().get("access_token")
    if not token:
        raise ZoomIntegrationError("Zoom access token missing in response")
    return token


def _pick_recording_file(recording_files: list[dict]) -> dict | None:
    for file in recording_files:
        if file.get("file_type") == "MP4":
            return file
    return recording_files[0] if recording_files else None


def download_meeting_recording(meeting_id: str) -> dict:
    """Download the primary Zoom cloud recording for a meeting."""

    access_token = _get_zoom_access_token()
    encoded_meeting_id = quote(meeting_id, safe="")
    url = f"https://api.zoom.us/v2/meetings/{encoded_meeting_id}/recordings"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to list Zoom recordings for meeting %s: %s", meeting_id, exc)
        raise ZoomIntegrationError("Failed to list Zoom recordings") from exc

    recording_files = resp.json().get("recording_files", [])
    target_file = _pick_recording_file(recording_files)
    if not target_file:
        raise ZoomIntegrationError("No Zoom recordings available for this meeting")

    download_url = target_file.get("download_url")
    if not download_url:
        raise ZoomIntegrationError("Zoom recording download URL missing")

    try:
        download_resp = requests.get(download_url, headers=headers, timeout=30)
        download_resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to download Zoom recording for meeting %s: %s", meeting_id, exc)
        raise ZoomIntegrationError("Failed to download Zoom recording") from exc

    file_name = target_file.get("file_name") or f"zoom-recording-{meeting_id}.mp4"
    mime_type = target_file.get("file_type")
    mime_type = "video/mp4" if mime_type == "MP4" or not mime_type else f"video/{mime_type.lower()}"

    return {
        "file_name": file_name,
        "mime_type": mime_type,
        "download_url": download_url,
        "content": download_resp.content,
    }


def delete_meeting_recordings(meeting_id: str) -> None:
    """Delete all Zoom cloud recordings for the given meeting ID."""

    access_token = _get_zoom_access_token()
    encoded_meeting_id = quote(meeting_id, safe="")
    url = f"https://api.zoom.us/v2/meetings/{encoded_meeting_id}/recordings"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.delete(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to delete Zoom recordings for meeting %s: %s", meeting_id, exc)
        raise ZoomIntegrationError("Failed to delete Zoom recordings") from exc


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
        logger.error("Failed to create Zoom meeting for user %s: %s", user_id, exc)
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
