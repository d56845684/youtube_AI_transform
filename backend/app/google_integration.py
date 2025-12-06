import json
import logging
import os
import asyncio
from datetime import datetime, timezone

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from . import models

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
]


class GoogleIntegrationError(Exception):
    """Raised when Google API interactions fail or are misconfigured."""


def _load_credentials():
    credentials_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE")

    if credentials_json:
        try:
            payload = json.loads(credentials_json)
        except json.JSONDecodeError as exc:
            raise GoogleIntegrationError("Invalid GOOGLE_CREDENTIALS_JSON payload") from exc
        return service_account.Credentials.from_service_account_info(payload, scopes=SCOPES)

    if credentials_file:
        return service_account.Credentials.from_service_account_file(credentials_file, scopes=SCOPES)

    raise GoogleIntegrationError(
        "Google credentials not configured. Set GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_FILE."
    )


def _append_booking_to_sheet(credentials, booking: models.LessonBooking, availability: models.TeacherAvailability, teacher: models.User, student: models.User):
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    worksheet_name = os.getenv("GOOGLE_SHEETS_WORKSHEET")

    if not sheet_id:
        logger.info("GOOGLE_SHEETS_ID is not set; skipping sheet sync")
        return

    client = gspread.authorize(credentials)
    worksheet = (
        client.open_by_key(sheet_id).worksheet(worksheet_name)
        if worksheet_name
        else client.open_by_key(sheet_id).sheet1
    )

    start_dt = (
        datetime.combine(booking.reserved_at.date(), availability.start_time)
        .replace(tzinfo=timezone.utc)
        .isoformat()
    )
    end_dt = (
        datetime.combine(booking.reserved_at.date(), availability.end_time)
        .replace(tzinfo=timezone.utc)
        .isoformat()
    )

    row = [
        booking.id,
        booking.reserved_at.replace(tzinfo=timezone.utc).isoformat(),
        teacher.full_name,
        teacher.email,
        student.full_name,
        student.email,
        availability.weekday,
        start_dt,
        end_dt,
        booking.platform,
        booking.conference_link,
    ]

    worksheet.append_row(row, value_input_option="USER_ENTERED")


def _create_calendar_event(credentials, booking: models.LessonBooking, availability: models.TeacherAvailability, teacher: models.User, student: models.User):
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
    if not calendar_id:
        logger.info("GOOGLE_CALENDAR_ID is not set; skipping calendar event creation")
        return

    calendar = build("calendar", "v3", credentials=credentials)
    start_time = datetime.combine(booking.reserved_at.date(), availability.start_time).replace(tzinfo=timezone.utc)
    end_time = datetime.combine(booking.reserved_at.date(), availability.end_time).replace(tzinfo=timezone.utc)

    event = {
        "summary": f"Lesson: {student.full_name} ↔ {teacher.full_name}",
        "description": f"Platform: {booking.platform}\nLink: {booking.conference_link}",
        "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
        "attendees": [{"email": teacher.email}, {"email": student.email}],
        "conferenceData": {
            "createRequest": {
                "requestId": f"booking-{booking.id}-{int(booking.reserved_at.timestamp())}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    calendar.events().insert(calendarId=calendar_id, body=event, conferenceDataVersion=1).execute()


async def sync_booking_to_google(*, booking: models.LessonBooking, availability: models.TeacherAvailability, teacher: models.User, student: models.User):
    """Push a confirmed booking to Google Sheets and Calendar."""

    credentials = await asyncio.to_thread(_load_credentials)
    try:
        await asyncio.to_thread(
            _append_booking_to_sheet, credentials, booking, availability, teacher, student
        )
        await asyncio.to_thread(
            _create_calendar_event, credentials, booking, availability, teacher, student
        )
    except (gspread.GSpreadException, HttpError) as exc:
        raise GoogleIntegrationError("Failed to synchronize booking with Google services") from exc
