import asyncio
import logging
import os
import uuid
from datetime import timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.ext.asyncio import AsyncSession

from . import models

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleIntegrationError(Exception):
    """Raised when Google API interactions fail or are misconfigured."""


def _get_credentials_file() -> str:
    return os.getenv("GOOGLE_OAUTH_CREDENTIALS_FILE", "credentials.json")


def _get_token_file() -> str:
    return os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "token.json")


def _load_credentials() -> Credentials:
    credentials_path = _get_credentials_file()
    token_path = _get_token_file()

    creds: Credentials | None = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise GoogleIntegrationError(
                    f"Google OAuth client file not found at '{credentials_path}'"
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return creds


def _extract_meet_link(event: dict) -> str | None:
    conference_data = event.get("conferenceData", {}) if event else {}
    entry_points = conference_data.get("entryPoints", [])
    for entry_point in entry_points:
        if entry_point.get("entryPointType") == "video":
            return entry_point.get("uri")
    return None


async def create_calendar_event_for_booking(
    *,
    db: AsyncSession,
    booking: models.LessonBooking,
    availability: models.TeacherAvailability,
    teacher: models.User,
    student: models.User,
    reserved_by_email: str,
) -> models.GoogleCalendarEvent:
    """Create a Google Calendar event and persist it with attendee emails."""

    credentials = await asyncio.to_thread(_load_credentials)
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    start_dt = availability.start_time.astimezone(timezone.utc)
    end_dt = availability.end_time.astimezone(timezone.utc)

    summary = f"Lesson: {student.full_name} ↔ {teacher.full_name}"
    description = f"Platform: {booking.platform}\nLink: {booking.conference_link}"
    attendee_emails = sorted({teacher.email, student.email})

    def _insert_event() -> dict:
        service = build("calendar", "v3", credentials=credentials)
        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": email} for email in attendee_emails],
            "conferenceData": {
                "createRequest": {
                    "requestId": f"booking-{booking.id}-{uuid.uuid4()}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }
        return (
            service.events()
            .insert(calendarId=calendar_id, body=event_body, conferenceDataVersion=1)
            .execute()
        )

    try:
        event = await asyncio.to_thread(_insert_event)
    except HttpError as exc:
        raise GoogleIntegrationError("Failed to create calendar event") from exc

    meet_link = _extract_meet_link(event)

    record = models.GoogleCalendarEvent(
        booking_id=booking.id,
        calendar_event_id=event.get("id", ""),
        calendar_id=calendar_id,
        summary=summary,
        description=description,
        meet_link=meet_link,
        start_at=start_dt,
        end_at=end_dt,
        creator_email=reserved_by_email,
        attendee_emails=",".join(attendee_emails),
    )

    db.add(record)
    await db.flush()

    return record
