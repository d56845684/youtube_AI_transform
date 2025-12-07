from datetime import datetime, timedelta, timezone
from enum import Enum
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum as PgEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from .database import Base


UTC_PLUS_8 = timezone(timedelta(hours=8))


def now_in_utc_plus_8() -> datetime:
    return datetime.now(UTC_PLUS_8)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=now_in_utc_plus_8, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=now_in_utc_plus_8, onupdate=now_in_utc_plus_8, nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    SUPERUSER = "superuser"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(PgEnum(UserRole, name="user_role"), nullable=False)

    availabilities = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete")
    bookings = relationship("LessonBooking", back_populates="student", foreign_keys="LessonBooking.student_id")
    lessons = relationship("LessonBooking", back_populates="teacher", foreign_keys="LessonBooking.teacher_id")
    orders = relationship("Order", back_populates="student", cascade="all, delete")


class TeacherAvailability(TimestampMixin, Base):
    __tablename__ = "teacher_availabilities"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    availability_date = Column(Date, nullable=False)
    weekday = Column(String, nullable=False)
    start_time = Column(Time(timezone=True), nullable=False)
    end_time = Column(Time(timezone=True), nullable=False)
    is_booked = Column(Integer, default=0, nullable=False)

    teacher = relationship("User", back_populates="availabilities")
    booking = relationship("LessonBooking", back_populates="availability", uselist=False)


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_total = Column(Numeric(10, 2), nullable=False)
    lesson_credits = Column(Integer, nullable=False)
    coupon_code = Column(String, nullable=True)

    student = relationship("User", back_populates="orders")


class LessonBooking(TimestampMixin, Base):
    __tablename__ = "lesson_bookings"

    id = Column(Integer, primary_key=True)
    availability_id = Column(Integer, ForeignKey("teacher_availabilities.id", ondelete="SET NULL"), nullable=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reserved_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC_PLUS_8), nullable=False
    )
    platform = Column(String, nullable=False, default="Google Meet")
    conference_link = Column(String, nullable=False)

    availability = relationship("TeacherAvailability", back_populates="booking")
    student = relationship("User", foreign_keys=[student_id], back_populates="bookings")
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="lessons")


class MeetingRecord(TimestampMixin, Base):
    __tablename__ = "meeting_records"

    id = Column(Integer, primary_key=True)
    booking_id = Column(
        Integer, ForeignKey("lesson_bookings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    reserved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    platform = Column(String, nullable=False)
    conference_link = Column(String, nullable=False)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    teacher_email = Column(String, nullable=False)
    student_email = Column(String, nullable=False)
    participant_emails = Column(String, nullable=True)

    booking = relationship("LessonBooking")
    reserved_by = relationship("User")


class GoogleCalendarEvent(TimestampMixin, Base):
    __tablename__ = "google_calendar_events"

    id = Column(Integer, primary_key=True)
    booking_id = Column(
        Integer, ForeignKey("lesson_bookings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    calendar_event_id = Column(String, nullable=False, unique=True)
    calendar_id = Column(String, nullable=False, default="primary")
    summary = Column(String, nullable=False)
    description = Column(String, nullable=True)
    meet_link = Column(String, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    creator_email = Column(String, nullable=False)
    attendee_emails = Column(String, nullable=True)

    booking = relationship("LessonBooking")
