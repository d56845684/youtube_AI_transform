from datetime import date, datetime, time
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, constr


class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"
    superuser = "superuser"


class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    full_name: constr(min_length=1)
    role: UserRole


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserPublic(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: UserRole


class AvailabilityCreate(BaseModel):
    availability_date: date
    start_time: time
    end_time: time


class AvailabilityUpdate(BaseModel):
    availability_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    is_booked: Optional[int] = None


class AvailabilityOut(BaseModel):
    id: int
    teacher_id: int
    teacher: Optional[UserPublic]
    availability_date: date
    weekday: str
    start_time: time
    end_time: time
    is_booked: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True


class BookingCreate(BaseModel):
    availability_id: int
    platform: constr(regex="^(Google Meet|Zoom|VOOM)$")


class BookingUpdate(BaseModel):
    platform: Optional[constr(regex="^(Google Meet|Zoom|VOOM)$")]
    conference_link: Optional[str]


class BookingStatus(str, Enum):
    success = "成功"
    cancelled = "取消"


class BookingOut(BaseModel):
    id: int
    availability: Optional[AvailabilityOut]
    student_id: int
    teacher_id: int
    student: Optional[UserPublic]
    teacher: Optional[UserPublic]
    platform: str
    conference_link: str
    zoom_recording: Optional["ZoomRecordingOut"]
    status: BookingStatus
    status_desc: Optional[str]
    reserved_at: datetime
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True


class BookingCancel(BaseModel):
    status_desc: Optional[str] = None


class OrderCreate(BaseModel):
    order_total: float
    lesson_credits: int
    coupon_code: Optional[str] = None


class OrderUpdate(BaseModel):
    order_total: Optional[float]
    lesson_credits: Optional[int]
    coupon_code: Optional[str]


class OrderOut(BaseModel):
    id: int
    order_total: float
    lesson_credits: int
    coupon_code: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True


class MeetingRecordCreate(BaseModel):
    booking_id: int
    reserved_by_id: Optional[int] = None
    platform: str
    conference_link: str
    start_at: datetime
    end_at: datetime
    teacher_email: EmailStr
    student_email: EmailStr
    participant_emails: Optional[str] = None


class MeetingRecordUpdate(BaseModel):
    reserved_by_id: Optional[int]
    platform: Optional[str]
    conference_link: Optional[str]
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    teacher_email: Optional[EmailStr]
    student_email: Optional[EmailStr]
    participant_emails: Optional[str]


class MeetingRecordOut(BaseModel):
    id: int
    booking_id: int
    reserved_by_id: Optional[int]
    platform: str
    conference_link: str
    start_at: datetime
    end_at: datetime
    teacher_email: EmailStr
    student_email: EmailStr
    participant_emails: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True


class CalendarEventCreate(BaseModel):
    booking_id: int
    calendar_event_id: str
    calendar_id: Optional[str] = "primary"
    summary: str
    description: Optional[str] = None
    meet_link: Optional[str] = None
    start_at: datetime
    end_at: datetime
    creator_email: EmailStr
    attendee_emails: Optional[str] = None


class CalendarEventUpdate(BaseModel):
    calendar_event_id: Optional[str]
    calendar_id: Optional[str]
    summary: Optional[str]
    description: Optional[str]
    meet_link: Optional[str]
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    creator_email: Optional[EmailStr]
    attendee_emails: Optional[str]


class ZoomRecordingRequest(BaseModel):
    share_email: EmailStr
    meeting_id: Optional[str] = None


class ZoomRecordingOut(BaseModel):
    id: int
    booking_id: int
    meeting_id: str
    file_name: Optional[str]
    recording_download_url: Optional[str]
    drive_file_id: Optional[str]
    drive_share_link: Optional[str]
    shared_with_email: Optional[str]
    start_url: Optional[str]
    join_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True


class CalendarEventOut(BaseModel):
    id: int
    booking_id: int
    calendar_event_id: str
    calendar_id: str
    summary: str
    description: Optional[str]
    meet_link: Optional[str]
    start_at: datetime
    end_at: datetime
    creator_email: EmailStr
    attendee_emails: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    full_name: Optional[constr(min_length=1)]
    role: Optional[UserRole]
    password: Optional[constr(min_length=8)]
