"""
Integration-style test that walks through creating users and booking a Google Meet.

The test is intentionally defensive: it will skip if the backend is not reachable
or if Google OAuth credentials are not available. Set ``BACKEND_BASE_URL`` to point
at a running FastAPI instance and ensure ``GOOGLE_OAUTH_CREDENTIALS_FILE`` points to
an authorized OAuth client JSON file with Calendar scopes enabled.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest


BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
CREDENTIALS_FILE = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE", "credentials.json")


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _ensure_backend_available(client: httpx.AsyncClient) -> None:
    try:
        response = await client.get("/docs")
        response.raise_for_status()
    except httpx.ConnectError as exc:  # pragma: no cover - network guard
        pytest.skip(f"Backend not reachable at {BACKEND_BASE_URL}: {exc}")
    except httpx.HTTPStatusError as exc:  # pragma: no cover - misconfigured backend
        pytest.skip(f"Backend reachable but returned error for /docs: {exc}")


@pytest.mark.integration
@pytest.mark.asyncio(scope="session")
async def test_google_meet_booking_flow() -> None:
    if not os.path.exists(CREDENTIALS_FILE):
        pytest.skip(
            "Google OAuth credentials file missing; provide GOOGLE_OAUTH_CREDENTIALS_FILE to run."
        )

    unique_suffix = uuid.uuid4().hex[:8]
    teacher_email = f"teacher_{unique_suffix}@example.com"
    student_email = f"student_{unique_suffix}@example.com"
    password = "P@ssword123"

    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL, timeout=15.0) as client:
        await _ensure_backend_available(client)

        # Register users
        for email, role in ((teacher_email, "teacher"), (student_email, "student")):
            response = await client.post(
                "/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "full_name": f"{role.title()} {unique_suffix}",
                    "role": role,
                },
            )
            response.raise_for_status()

        # Authenticate both accounts
        async def login(email: str) -> str:
            token_response = await client.post(
                "/auth/token",
                data={"username": email, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            return token_data["access_token"]

        teacher_token, student_token = await login(teacher_email), await login(student_email)

        # Teacher publishes availability 24 hours from now for a 1-hour lesson
        start_time = (
            datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            + timedelta(days=1)
        )
        end_time = start_time + timedelta(hours=1)
        weekday = start_time.strftime("%A")

        availability_response = await client.post(
            "/teachers/availability",
            json={
                "weekday": weekday,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            },
            headers=_auth_headers(teacher_token),
        )
        availability_response.raise_for_status()
        availability_id = availability_response.json()["id"]

        # Student books the slot on Google Meet
        booking_response = await client.post(
            "/bookings",
            json={"availability_id": availability_id, "platform": "Google Meet"},
            headers=_auth_headers(student_token),
        )
        booking_response.raise_for_status()
        booking = booking_response.json()

        assert booking["platform"] == "Google Meet"
        assert booking["conference_link"].startswith("https://meet.google.com/")
        assert booking["student_id"] != booking["teacher_id"]
