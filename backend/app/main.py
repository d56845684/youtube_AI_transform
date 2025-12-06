from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import auth, models, schemas
from .database import Base, engine, get_db

app = FastAPI(title="Language Tutor Marketplace")


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_teacher(user: models.User) -> None:
    if user.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher role required")


def ensure_student(user: models.User) -> None:
    if user.role != models.UserRole.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student role required")


@app.post("/auth/register", response_model=schemas.UserOut)
async def register(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(models.User).where(models.User.email == user_in.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    hashed_password = auth.get_password_hash(user_in.password)
    user = models.User(
        email=user_in.email,
        full_name=user_in.full_name,
        role=models.UserRole(user_in.role.value),
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.post("/auth/token", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth.create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/teachers/availability", response_model=schemas.AvailabilityOut)
async def create_availability(
    payload: schemas.AvailabilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ensure_teacher(current_user)
    availability = models.TeacherAvailability(
        teacher_id=current_user.id,
        weekday=payload.weekday,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(availability)
    await db.commit()
    await db.refresh(availability)
    return availability


@app.get("/teachers/{teacher_id}/availability", response_model=list[schemas.AvailabilityOut])
async def list_availability(teacher_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.TeacherAvailability).where(models.TeacherAvailability.teacher_id == teacher_id)
    )
    return result.scalars().all()


@app.post("/bookings", response_model=schemas.BookingOut)
async def book_availability(
    payload: schemas.BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ensure_student(current_user)
    availability_result = await db.execute(
        select(models.TeacherAvailability).where(models.TeacherAvailability.id == payload.availability_id)
    )
    availability = availability_result.scalar_one_or_none()
    if availability is None or availability.is_booked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found or already booked")

    teacher_result = await db.execute(select(models.User).where(models.User.id == availability.teacher_id))
    teacher = teacher_result.scalar_one_or_none()
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher unavailable")

    platform_domain = "meet.google.com" if payload.platform == "Google Meet" else "voom.com"
    conference_link = f"https://{platform_domain}/{teacher.id}-{current_user.id}-{int(datetime.utcnow().timestamp())}"

    availability.is_booked = 1
    booking = models.LessonBooking(
        availability_id=availability.id,
        student_id=current_user.id,
        teacher_id=teacher.id,
        platform=payload.platform,
        conference_link=conference_link,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)

    start_dt = datetime.combine(booking.reserved_at.date(), availability.start_time)
    end_dt = datetime.combine(booking.reserved_at.date(), availability.end_time)

    meeting_record = models.MeetingRecord(
        booking_id=booking.id,
        reserved_by_id=current_user.id,
        platform=booking.platform,
        conference_link=booking.conference_link,
        start_at=start_dt,
        end_at=end_dt,
        teacher_email=teacher.email,
        student_email=current_user.email,
        participant_emails=",".join(sorted({teacher.email, current_user.email})),
    )
    db.add(meeting_record)
    await db.commit()
    return booking


@app.post("/orders", response_model=schemas.OrderOut)
async def create_order(
    payload: schemas.OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ensure_student(current_user)
    order = models.Order(
        student_id=current_user.id,
        order_total=payload.order_total,
        lesson_credits=payload.lesson_credits,
        coupon_code=payload.coupon_code,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@app.get("/bookings", response_model=list[schemas.BookingOut])
async def list_bookings(
    current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)
):
    if current_user.role == models.UserRole.TEACHER:
        result = await db.execute(select(models.LessonBooking).where(models.LessonBooking.teacher_id == current_user.id))
    else:
        result = await db.execute(select(models.LessonBooking).where(models.LessonBooking.student_id == current_user.id))
    return result.scalars().all()
