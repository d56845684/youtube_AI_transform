"""Endpoint-focused integration checks for the Google Meet booking flow.

Each test targets a single endpoint to make it easier to fan out across
independent CI jobs. Only the booking test requires Google OAuth credentials;
the others simply exercise the API contracts for registration, login, and
availability.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import pytest
import pytest_asyncio


BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")


@dataclass
class TestContext:
    teacher_email: str
    student_email: str
    password: str


def _find_credentials_file() -> Path | None:
    """Return the first usable Google OAuth credentials file, if present."""

    env_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE")
    candidates = [Path(env_path).expanduser()] if env_path else []

    repo_default = Path(__file__).resolve().parent.parent / "credentials.json"
    candidates.append(repo_default)
    candidates.append(Path.cwd() / "credentials.json")

    for path in candidates:
        if path.is_file():
            return path
    return None


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


async def _register_user(
    client: httpx.AsyncClient, *, email: str, role: str, password: str, full_name: str
) -> httpx.Response:
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "role": role,
        },
    )
    response.raise_for_status()
    return response


async def _login(client: httpx.AsyncClient, *, email: str, password: str) -> str:
    token_response = await client.post(
        "/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_response.raise_for_status()
    return token_response.json()["access_token"]


@pytest.fixture(scope="function")
def test_context() -> TestContext:
    suffix = uuid.uuid4().hex[:8]
    password = "P@ssword123"
    return TestContext(
        teacher_email=f"teacher_{suffix}@example.com",
        student_email=f"student_{suffix}@example.com",
        password=password,
    )


@pytest_asyncio.fixture(scope="session")
async def client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(base_url=BACKEND_BASE_URL, timeout=15.0) as client:
        await _ensure_backend_available(client)
        yield client


pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_register_users(client: httpx.AsyncClient, test_context: TestContext) -> None:
    """Teachers and students can register."""

    teacher = await _register_user(
        client,
        email=test_context.teacher_email,
        role="teacher",
        password=test_context.password,
        full_name="Teacher Test",
    )
    student = await _register_user(
        client,
        email=test_context.student_email,
        role="student",
        password=test_context.password,
        full_name="Student Test",
    )

    assert teacher.status_code == 200
    assert student.status_code == 200


@pytest.mark.asyncio
async def test_login_users(client: httpx.AsyncClient, test_context: TestContext) -> None:
    """Registered users can obtain access tokens."""

    await _register_user(
        client,
        email=test_context.teacher_email,
        role="teacher",
        password=test_context.password,
        full_name="Teacher Login",
    )
    await _register_user(
        client,
        email=test_context.student_email,
        role="student",
        password=test_context.password,
        full_name="Student Login",
    )

    teacher_token = await _login(client, email=test_context.teacher_email, password=test_context.password)
    student_token = await _login(client, email=test_context.student_email, password=test_context.password)

    assert isinstance(teacher_token, str) and teacher_token
    assert isinstance(student_token, str) and student_token


@pytest.mark.asyncio
async def test_publish_availability(client: httpx.AsyncClient, test_context: TestContext) -> None:
    """Teachers can publish availability slots."""

    await _register_user(
        client,
        email=test_context.teacher_email,
        role="teacher",
        password=test_context.password,
        full_name="Teacher Availability",
    )
    teacher_token = await _login(client, email=test_context.teacher_email, password=test_context.password)

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
    availability_payload = availability_response.json()

    assert availability_payload["weekday"] == weekday
    assert availability_payload["start_time"].startswith(start_time.isoformat()[:16])
    assert availability_payload["end_time"].startswith(end_time.isoformat()[:16])


@pytest.mark.asyncio
async def test_book_google_meet(client: httpx.AsyncClient, test_context: TestContext) -> None:
    """Students can book a Google Meet session for a published slot."""

    if not _find_credentials_file():
        pytest.skip(
            "Google OAuth credentials file not found in $GOOGLE_OAUTH_CREDENTIALS_FILE, "
            "backend/credentials.json, or ./credentials.json."
        )

    await _register_user(
        client,
        email=test_context.teacher_email,
        role="teacher",
        password=test_context.password,
        full_name="Teacher Booking",
    )
    await _register_user(
        client,
        email=test_context.student_email,
        role="student",
        password=test_context.password,
        full_name="Student Booking",
    )

    teacher_token = await _login(client, email=test_context.teacher_email, password=test_context.password)
    student_token = await _login(client, email=test_context.student_email, password=test_context.password)

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
