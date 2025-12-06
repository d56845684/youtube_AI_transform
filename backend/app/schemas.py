from datetime import datetime, time
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, constr


class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"


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

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int
    role: UserRole


class AvailabilityCreate(BaseModel):
    weekday: constr(min_length=3)
    start_time: time
    end_time: time


class AvailabilityOut(BaseModel):
    id: int
    weekday: str
    start_time: time
    end_time: time
    is_booked: int

    class Config:
        orm_mode = True


class BookingCreate(BaseModel):
    availability_id: int
    platform: constr(regex="^(Google Meet|VOOM)$")


class BookingOut(BaseModel):
    id: int
    availability: Optional[AvailabilityOut]
    student_id: int
    teacher_id: int
    conference_link: str
    reserved_at: datetime

    class Config:
        orm_mode = True


class OrderCreate(BaseModel):
    order_total: float
    lesson_credits: int
    coupon_code: Optional[str] = None


class OrderOut(BaseModel):
    id: int
    order_total: float
    lesson_credits: int
    coupon_code: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
