import logging
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from . import auth, google_integration, models, schemas
from .database import Base, engine, get_db

app = FastAPI(title="Language Tutor Marketplace")

logger = logging.getLogger(__name__)


def normalize_to_utc_plus_8(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=models.UTC_PLUS_8)
    return moment.astimezone(models.UTC_PLUS_8)


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        # Ensure legacy databases have the platform column on lesson bookings
        await conn.execute(
            text(
                """
                ALTER TABLE lesson_bookings
                ADD COLUMN IF NOT EXISTS platform VARCHAR NOT NULL DEFAULT 'Google Meet';
                """
            )
        )

        timezone_migrations = [
            """
            ALTER TABLE IF EXISTS teacher_availabilities
            ALTER COLUMN start_time TYPE TIMESTAMP WITH TIME ZONE
            USING ((CURRENT_DATE + start_time)::timestamp AT TIME ZONE '+08');
            """,
            """
            ALTER TABLE IF EXISTS teacher_availabilities
            ALTER COLUMN end_time TYPE TIMESTAMP WITH TIME ZONE
            USING ((CURRENT_DATE + end_time)::timestamp AT TIME ZONE '+08');
            """,
            """
            ALTER TABLE IF EXISTS users
            ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
            USING (created_at AT TIME ZONE 'UTC'),
            ALTER COLUMN created_at SET DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE '+08');
            """,
            """
            ALTER TABLE IF EXISTS orders
            ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
            USING (created_at AT TIME ZONE 'UTC'),
            ALTER COLUMN created_at SET DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE '+08');
            """,
            """
            ALTER TABLE IF EXISTS lesson_bookings
            ALTER COLUMN reserved_at TYPE TIMESTAMP WITH TIME ZONE
            USING (reserved_at AT TIME ZONE 'UTC'),
            ALTER COLUMN reserved_at SET DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE '+08');
            """,
            """
            ALTER TABLE IF EXISTS meeting_records
            ALTER COLUMN start_at TYPE TIMESTAMP WITH TIME ZONE
            USING (start_at AT TIME ZONE 'UTC'),
            ALTER COLUMN end_at TYPE TIMESTAMP WITH TIME ZONE
            USING (end_at AT TIME ZONE 'UTC');
            """,
            """
            ALTER TABLE IF EXISTS google_calendar_events
            ALTER COLUMN start_at TYPE TIMESTAMP WITH TIME ZONE
            USING (start_at AT TIME ZONE 'UTC'),
            ALTER COLUMN end_at TYPE TIMESTAMP WITH TIME ZONE
            USING (end_at AT TIME ZONE 'UTC');
            """,
        ]

        for statement in timezone_migrations:
            await conn.execute(text(statement))
        await conn.run_sync(Base.metadata.create_all)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_teacher(user: models.User) -> None:
    if user.role not in {models.UserRole.TEACHER, models.UserRole.SUPERUSER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher role required")


def ensure_student(user: models.User) -> None:
    if user.role not in {models.UserRole.STUDENT, models.UserRole.SUPERUSER}:
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
        start_time=normalize_to_utc_plus_8(payload.start_time),
        end_time=normalize_to_utc_plus_8(payload.end_time),
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
    now_ts = int(datetime.now(tz=models.UTC_PLUS_8).timestamp())
    conference_link = f"https://{platform_domain}/{teacher.id}-{current_user.id}-{now_ts}"

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

    google_event: models.GoogleCalendarEvent | None = None
    try:
        google_event = await google_integration.create_calendar_event_for_booking(
            db=db,
            booking=booking,
            availability=availability,
            teacher=teacher,
            student=current_user,
            reserved_by_email=current_user.email,
        )
    except google_integration.GoogleIntegrationError as exc:
        logger.warning("Failed to sync booking to Google Calendar: %s", exc)

    if google_event and google_event.meet_link:
        booking.conference_link = google_event.meet_link
        booking.platform = "Google Meet"
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

    start_dt = normalize_to_utc_plus_8(availability.start_time)
    end_dt = normalize_to_utc_plus_8(availability.end_time)

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


@app.get("/orders", response_model=list[schemas.OrderOut])
async def list_orders(
    db: AsyncSession = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    ensure_student(current_user)
    if current_user.role == models.UserRole.SUPERUSER:
        result = await db.execute(select(models.Order))
    else:
        result = await db.execute(select(models.Order).where(models.Order.student_id == current_user.id))
    return result.scalars().all()


@app.get("/bookings", response_model=list[schemas.BookingOut])
async def list_bookings(
    current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)
):
    if current_user.role == models.UserRole.SUPERUSER:
        result = await db.execute(select(models.LessonBooking))
    elif current_user.role == models.UserRole.TEACHER:
        result = await db.execute(
            select(models.LessonBooking).where(models.LessonBooking.teacher_id == current_user.id)
        )
    else:
        result = await db.execute(
            select(models.LessonBooking).where(models.LessonBooking.student_id == current_user.id)
        )
    return result.scalars().all()
