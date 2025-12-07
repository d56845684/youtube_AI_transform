import asyncio
import io
import os
import uuid
from datetime import datetime, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from .logger import get_logger

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive.file",
]


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
            try:
                creds.refresh(Request())
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to refresh Google credentials: %s", exc)
                raise GoogleIntegrationError("Failed to refresh Google credentials") from exc
        else:
            if not os.path.exists(credentials_path):
                logger.error(
                    "Google OAuth client file not found at '%s'", credentials_path
                )
                raise GoogleIntegrationError(
                    f"Google OAuth client file not found at '{credentials_path}'"
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            try:
                creds = flow.run_local_server(port=0)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to complete Google OAuth flow: %s", exc)
                raise GoogleIntegrationError("Failed to load Google OAuth credentials") from exc

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
    conference_solution_type: str | None = "hangoutsMeet",
    extra_description_lines: list[str] | None = None,
) -> models.GoogleCalendarEvent:
    """Create a Google Calendar event and persist it with attendee emails."""

    credentials = await asyncio.to_thread(_load_credentials)
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

    start_dt = (
        datetime.combine(availability.availability_date, availability.start_time)
        .replace(tzinfo=models.UTC_PLUS_8)
        .astimezone(timezone.utc)
    )
    end_dt = (
        datetime.combine(availability.availability_date, availability.end_time)
        .replace(tzinfo=models.UTC_PLUS_8)
        .astimezone(timezone.utc)
    )

    summary = f"Lesson: {student.full_name} ↔ {teacher.full_name}"
    description_lines = [
        f"Platform: {booking.platform}",
        f"Link: {booking.conference_link}",
        *(extra_description_lines or []),
    ]
    description = "\n".join(description_lines)
    attendee_emails = sorted({teacher.email, student.email})

    def _insert_event() -> dict:
        service = build("calendar", "v3", credentials=credentials)
        event_body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": email} for email in attendee_emails],
        }
        if conference_solution_type:
            event_body["conferenceData"] = {
                "createRequest": {
                    "requestId": f"booking-{booking.id}-{uuid.uuid4()}",
                    "conferenceSolutionKey": {"type": conference_solution_type},
                }
            }
        return (
            service.events()
            .insert(calendarId=calendar_id, body=event_body, conferenceDataVersion=1)
            .execute()
        )

    try:
        event = await asyncio.to_thread(_insert_event)
    except HttpError as exc:
        logger.error("Failed to create calendar event for booking %s: %s", booking.id, exc)
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


async def delete_calendar_event(calendar_event: models.GoogleCalendarEvent) -> None:
    """Delete a Google Calendar event for all attendee emails."""

    credentials = await asyncio.to_thread(_load_credentials)
    calendar_id = calendar_event.calendar_id or os.getenv("GOOGLE_CALENDAR_ID", "primary")

    def _delete_event() -> None:
        service = build("calendar", "v3", credentials=credentials)
        (
            service.events()
            .delete(
                calendarId=calendar_id,
                eventId=calendar_event.calendar_event_id,
                sendUpdates="all",
            )
            .execute()
        )

    try:
        await asyncio.to_thread(_delete_event)
    except HttpError as exc:
        logger.error(
            "Failed to delete calendar event %s from calendar %s: %s",
            calendar_event.calendar_event_id,
            calendar_id,
            exc,
        )
        raise GoogleIntegrationError("Failed to delete calendar event") from exc


async def upload_file_to_drive(
    *,
    file_name: str,
    mime_type: str,
    content: bytes,
    share_email: str,
    folder_id: str | None = None,
) -> dict:
    """Upload a file to Google Drive and grant read access to the given email."""

    credentials = await asyncio.to_thread(_load_credentials)

    def _upload() -> dict:
        service = build("drive", "v3", credentials=credentials)
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=False)
        metadata: dict[str, object] = {"name": file_name}
        if folder_id:
            metadata["parents"] = [folder_id]

        file_resource = (
            service.files()
            .create(body=metadata, media_body=media, fields="id, webViewLink, webContentLink")
            .execute()
        )

        service.permissions().create(
            fileId=file_resource["id"],
            body={
                "type": "user",
                "role": "reader",
                "emailAddress": share_email,
            },
            fields="id",
            sendNotificationEmail=False,
        ).execute()

        return file_resource

    try:
        uploaded = await asyncio.to_thread(_upload)
    except HttpError as exc:
        logger.error("Failed to upload %s to Google Drive: %s", file_name, exc)
        raise GoogleIntegrationError("Failed to upload file to Google Drive") from exc

    logger.info("Uploaded file %s to Drive with id %s", file_name, uploaded.get("id"))
    return uploaded
