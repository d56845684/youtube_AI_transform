"""Step-by-step synchronous Google Meet booking check with logging.

This script exercises the backend endpoints in order without pytest. Each
step logs whether it succeeds or fails so it can be run manually or inside a
job runner that expects explicit progress reporting.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx


BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class TestContext:
    teacher_email: str
    student_email: str
    password: str
    teacher_token: str | None = None
    student_token: str | None = None
    availability_id: int | None = None


def _find_credentials_file() -> Path | None:
    env_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
    candidates = [Path(env_path).expanduser()] if env_path else []

    repo_default = Path(__file__).resolve().parent.parent / "credentials.json"
    candidates.append(repo_default)
    candidates.append(Path.cwd() / "credentials.json")

    for path in candidates:
        if path.is_file():
            return path
    return None


def ensure_backend_available(client: httpx.Client) -> bool:
    try:
        response = client.get("/docs")
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Backend unavailable at %s: %s", BACKEND_BASE_URL, exc)
        return False

    logger.info("Backend is reachable at %s", BACKEND_BASE_URL)
    return True


def register_user(
    client: httpx.Client, *, email: str, role: str, password: str, full_name: str
) -> bool:
    try:
        response = client.post(
            "/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": role,
            },
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Failed to register %s (%s): %s", email, role, exc)
        return False

    logger.info("Registered %s (%s)", email, role)
    return True


def login_user(client: httpx.Client, *, email: str, password: str) -> str | None:
    try:
        response = client.post(
            "/auth/token",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        token = response.json()["access_token"]
    except httpx.HTTPError as exc:
        logger.error("Failed to login %s: %s", email, exc)
        return None

    logger.info("Logged in %s", email)
    return token


def publish_availability(client: httpx.Client, context: TestContext) -> bool:
    start_time = (
        datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        + timedelta(days=1)
    )
    end_time = start_time + timedelta(hours=1)
    weekday = start_time.strftime("%A")

    try:
        response = client.post(
            "/teachers/availability",
            json={
                "weekday": weekday,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            headers={"Authorization": f"Bearer {context.teacher_token}"},
        )
        response.raise_for_status()
        context.availability_id = response.json()["id"]
    except httpx.HTTPError as exc:
        logger.error("Failed to publish availability: %s", exc)
        return False

    logger.info(
        "Published availability %s for %s from %s to %s",
        context.availability_id,
        weekday,
        start_time.isoformat(),
        end_time.isoformat(),
    )
    return True


def book_google_meet(client: httpx.Client, context: TestContext) -> bool:
    credentials_path = _find_credentials_file()
    if not credentials_path:
        logger.error(
            "Missing Google OAuth credentials. Provide GOOGLE_OAUTH_CREDENTIALS_FILE or credentials.json"
        )
        return False

    try:
        response = client.post(
            "/bookings",
            json={
                "availability_id": context.availability_id,
                "platform": "Google Meet",
            },
            headers={"Authorization": f"Bearer {context.student_token}"},
        )
        response.raise_for_status()
        booking = response.json()
    except httpx.HTTPError as exc:
        logger.error("Failed to book Google Meet: %s", exc)
        return False

    logger.info(
        "Booked Google Meet with link %s for availability %s",
        booking.get("conference_link", "<missing>"),
        context.availability_id,
    )
    return True


def run_flow() -> int:
    suffix = uuid.uuid4().hex[:8]
    context = TestContext(
        teacher_email=f"teacher_{suffix}@example.com",
        student_email=f"student_{suffix}@example.com",
        password="P@ssword123",
    )

    with httpx.Client(base_url=BACKEND_BASE_URL, timeout=15.0) as client:
        if not ensure_backend_available(client):
            return 1

        if not register_user(
            client,
            email=context.teacher_email,
            role="teacher",
            password=context.password,
            full_name="Teacher Sync Test",
        ):
            return 1

        if not register_user(
            client,
            email=context.student_email,
            role="student",
            password=context.password,
            full_name="Student Sync Test",
        ):
            return 1

        context.teacher_token = login_user(
            client, email=context.teacher_email, password=context.password
        )
        context.student_token = login_user(
            client, email=context.student_email, password=context.password
        )
        if not context.teacher_token or not context.student_token:
            return 1

        if not publish_availability(client, context):
            return 1

        if not book_google_meet(client, context):
            return 1

    logger.info("Google Meet flow completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(run_flow())
