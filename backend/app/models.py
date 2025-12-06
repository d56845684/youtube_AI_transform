from datetime import datetime, time
from enum import Enum
from sqlalchemy import Column, DateTime, Enum as PgEnum, ForeignKey, Integer, Numeric, String, Time
from sqlalchemy.orm import relationship

from .database import Base


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(PgEnum(UserRole, name="user_role"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    availabilities = relationship("TeacherAvailability", back_populates="teacher", cascade="all, delete")
    bookings = relationship("LessonBooking", back_populates="student", foreign_keys="LessonBooking.student_id")
    lessons = relationship("LessonBooking", back_populates="teacher", foreign_keys="LessonBooking.teacher_id")
    orders = relationship("Order", back_populates="student", cascade="all, delete")


class TeacherAvailability(Base):
    __tablename__ = "teacher_availabilities"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    weekday = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_booked = Column(Integer, default=0, nullable=False)

    teacher = relationship("User", back_populates="availabilities")
    booking = relationship("LessonBooking", back_populates="availability", uselist=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    order_total = Column(Numeric(10, 2), nullable=False)
    lesson_credits = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    coupon_code = Column(String, nullable=True)

    student = relationship("User", back_populates="orders")


class LessonBooking(Base):
    __tablename__ = "lesson_bookings"

    id = Column(Integer, primary_key=True)
    availability_id = Column(Integer, ForeignKey("teacher_availabilities.id", ondelete="SET NULL"), nullable=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reserved_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    platform = Column(String, nullable=False, default="Google Meet")
    conference_link = Column(String, nullable=False)

    availability = relationship("TeacherAvailability", back_populates="booking")
    student = relationship("User", foreign_keys=[student_id], back_populates="bookings")
    teacher = relationship("User", foreign_keys=[teacher_id], back_populates="lessons")
