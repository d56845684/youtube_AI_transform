import asyncio
import os
from datetime import date, datetime, time
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from . import auth, google_integration, models, schemas, zoom_integration
from .database import Base, SessionLocal, engine, get_db
from .logger import get_logger

app = FastAPI(title="Language Tutor Marketplace")

logger = get_logger(__name__)


def normalize_to_utc_plus_8(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=models.UTC_PLUS_8)
    return moment.astimezone(models.UTC_PLUS_8)


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def ensure_seed_user(
        *, email: str | None, password: str | None, full_name: str | None, role: models.UserRole
    ) -> None:
        if not email or not password:
            logger.warning("Skip creating %s: missing email or password", role.value)
            return

        async with SessionLocal() as session:  # type: AsyncSession
            result = await session.execute(
                select(models.User).where(models.User.email == email, models.User.deleted_at.is_(None))
            )
            user = result.scalar_one_or_none()
            if user:
                if user.role != role:
                    user.role = role
                    await session.commit()
                    await session.refresh(user)
                    logger.info("Updated existing %s to role %s", email, role.value)
                return

            seeded_user = models.User(
                email=email,
                full_name=full_name or role.value.title(),
                role=role,
                hashed_password=auth.get_password_hash(password),
            )
            session.add(seeded_user)
            await session.commit()
            logger.info("Created default %s user %s from environment", role.value, email)

    await ensure_seed_user(
        email=os.getenv("ADMIN_EMAIL"),
        password=os.getenv("ADMIN_PASSWORD"),
        full_name=os.getenv("ADMIN_FULL_NAME", "Admin"),
        role=models.UserRole.ADMIN,
    )
    await ensure_seed_user(
        email=os.getenv("SUPERUSER_EMAIL"),
        password=os.getenv("SUPERUSER_PASSWORD"),
        full_name=os.getenv("SUPERUSER_FULL_NAME", "Superuser"),
        role=models.UserRole.SUPERUSER,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def ensure_teacher(user: models.User) -> None:
    if user.role not in {
        models.UserRole.TEACHER,
        models.UserRole.ADMIN,
        models.UserRole.SUPERUSER,
    }:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher role required")


def ensure_student(user: models.User) -> None:
    if user.role not in {
        models.UserRole.STUDENT,
        models.UserRole.ADMIN,
        models.UserRole.SUPERUSER,
    }:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student role required")


def ensure_superuser(user: models.User) -> None:
    if user.role not in {models.UserRole.ADMIN, models.UserRole.SUPERUSER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser role required")


def derive_weekday_name(avail_date: date) -> str:
    return avail_date.strftime("%a")


def ensure_time_with_timezone(slot_time: time) -> time:
    if slot_time.tzinfo is None:
        return slot_time.replace(tzinfo=models.UTC_PLUS_8)
    dummy_dt = datetime.combine(date.today(), slot_time)
    return dummy_dt.astimezone(models.UTC_PLUS_8).timetz()


async def assert_no_overlapping_slots(
    *,
    db: AsyncSession,
    teacher_id: int,
    availability_date: date,
    start_time: time,
    end_time: time,
    exclude_id: int | None = None,
) -> None:
    start_time = ensure_time_with_timezone(start_time)
    end_time = ensure_time_with_timezone(end_time)

    query = select(models.TeacherAvailability).where(
        models.TeacherAvailability.teacher_id == teacher_id,
        models.TeacherAvailability.availability_date == availability_date,
        models.TeacherAvailability.start_time < end_time,
        models.TeacherAvailability.end_time > start_time,
    )

    if exclude_id is not None:
        query = query.where(models.TeacherAvailability.id != exclude_id)

    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Time slot overlaps with an existing availability",
        )


def combine_availability_window(
    availability: models.TeacherAvailability,
) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(availability.availability_date, availability.start_time)
    end_dt = datetime.combine(availability.availability_date, availability.end_time)

    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=models.UTC_PLUS_8)
    else:
        start_dt = start_dt.astimezone(models.UTC_PLUS_8)

    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=models.UTC_PLUS_8)
    else:
        end_dt = end_dt.astimezone(models.UTC_PLUS_8)

    return start_dt, end_dt


async def get_booking_with_permission(
    booking_id: int, current_user: models.User, db: AsyncSession
) -> models.LessonBooking:
    result = await db.execute(
        select(models.LessonBooking)
        .options(
            selectinload(models.LessonBooking.availability).selectinload(
                models.TeacherAvailability.teacher
            ),
            selectinload(models.LessonBooking.student),
            selectinload(models.LessonBooking.teacher),
            selectinload(models.LessonBooking.zoom_recording),
        )
        .where(
            models.LessonBooking.id == booking_id,
            models.LessonBooking.deleted_at.is_(None),
        )
    )
    booking = result.scalar_one_or_none()
    if booking is None or booking.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if current_user.role in {models.UserRole.SUPERUSER, models.UserRole.ADMIN}:
        return booking

    if booking.teacher_id != current_user.id and booking.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access booking")
    return booking


async def get_order_with_permission(
    order_id: int, current_user: models.User, db: AsyncSession
) -> models.Order:
    result = await db.execute(
        select(models.Order).where(
            models.Order.id == order_id,
            models.Order.deleted_at.is_(None),
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if current_user.role not in {models.UserRole.SUPERUSER, models.UserRole.ADMIN} and order.student_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access order")
    return order


@app.post("/auth/register", response_model=schemas.UserOut, tags=["Auth"])
async def register(user_in: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    if user_in.role in {schemas.UserRole.admin, schemas.UserRole.superuser}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot self-register admin or superuser accounts",
        )

    existing = await db.execute(select(models.User).where(models.User.email == user_in.email))
    if existing.scalar_one_or_none():
        logger.warning("Registration blocked for duplicate email: %s", user_in.email)
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

    logger.info("Registered new user %s with role %s", user.email, user.role.value)
    return user


@app.post("/auth/token", response_model=schemas.Token, tags=["Auth"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        logger.warning("Failed login attempt for %s", form_data.username)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth.create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserOut, tags=["Users"])
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.get("/users", response_model=list[schemas.UserOut], tags=["Users"])
async def list_users(
    current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)
):
    ensure_superuser(current_user)
    result = await db.execute(select(models.User).where(models.User.deleted_at.is_(None)))
    return result.scalars().all()


@app.get("/users/{user_id}", response_model=schemas.UserOut, tags=["Users"])
async def get_user(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in {models.UserRole.SUPERUSER, models.UserRole.ADMIN} and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this user")

    result = await db.execute(
        select(models.User).where(models.User.id == user_id, models.User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.get("/admin/users/lookup", response_model=schemas.AdminUserLookup, tags=["Admin"])
async def admin_lookup_user(
    email: EmailStr,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ensure_superuser(current_user)
    user_result = await db.execute(
        select(models.User).where(models.User.email == email, models.User.deleted_at.is_(None))
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    bookings_query = (
        select(models.LessonBooking)
        .options(
            selectinload(models.LessonBooking.availability).selectinload(
                models.TeacherAvailability.teacher
            ),
            selectinload(models.LessonBooking.student),
            selectinload(models.LessonBooking.teacher),
            selectinload(models.LessonBooking.zoom_recording),
        )
        .where(
            models.LessonBooking.deleted_at.is_(None),
            or_(
                models.LessonBooking.student_id == user.id,
                models.LessonBooking.teacher_id == user.id,
            ),
        )
    )
    bookings_result = await db.execute(bookings_query)
    bookings = bookings_result.scalars().all()

    availabilities: list[models.TeacherAvailability] | None = None
    if user.role == models.UserRole.TEACHER:
        availability_result = await db.execute(
            select(models.TeacherAvailability)
            .options(selectinload(models.TeacherAvailability.teacher))
            .where(
                models.TeacherAvailability.teacher_id == user.id,
                models.TeacherAvailability.deleted_at.is_(None),
            )
        )
        availabilities = availability_result.scalars().all()

    return schemas.AdminUserLookup(user=user, bookings=bookings, availabilities=availabilities)


@app.get("/teachers", response_model=list[schemas.UserPublic], tags=["Users"])
async def list_teachers(search: str | None = None, db: AsyncSession = Depends(get_db)):
    query = select(models.User).where(
        models.User.role == models.UserRole.TEACHER,
        models.User.deleted_at.is_(None),
    )
    if search:
        query = query.where(models.User.full_name.ilike(f"%{search}%"))
    result = await db.execute(query)
    return result.scalars().all()


@app.put("/users/{user_id}", response_model=schemas.UserOut, tags=["Users"])
async def update_user(
    user_id: int,
    payload: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in {models.UserRole.SUPERUSER, models.UserRole.ADMIN} and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this user")

    result = await db.execute(
        select(models.User).where(models.User.id == user_id, models.User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        ensure_superuser(current_user)
        user.role = models.UserRole(payload.role.value)
    if payload.password is not None:
        user.hashed_password = auth.get_password_hash(payload.password)

    await db.commit()
    await db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ensure_superuser(current_user)
    result = await db.execute(
        select(models.User).where(models.User.id == user_id, models.User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.deleted_at = models.now_in_utc_plus_8()
    await db.commit()
    return None


@app.post("/teachers/availability", response_model=schemas.AvailabilityOut, tags=["Teacher Availability"])
async def create_availability(
    payload: schemas.AvailabilityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ensure_teacher(current_user)
    teacher_id = payload.teacher_id or current_user.id
    if payload.teacher_id and current_user.role not in {models.UserRole.ADMIN, models.UserRole.SUPERUSER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to manage other teachers")

    teacher_result = await db.execute(
        select(models.User).where(models.User.id == teacher_id, models.User.deleted_at.is_(None))
    )
    teacher = teacher_result.scalar_one_or_none()
    if teacher is None or teacher.role != models.UserRole.TEACHER:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher not found")

    if payload.start_time >= payload.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be later than start time",
        )

    normalized_start = ensure_time_with_timezone(payload.start_time)
    normalized_end = ensure_time_with_timezone(payload.end_time)

    await assert_no_overlapping_slots(
        db=db,
        teacher_id=teacher_id,
        availability_date=payload.availability_date,
        start_time=normalized_start,
        end_time=normalized_end,
    )

    availability = models.TeacherAvailability(
        teacher_id=teacher_id,
        availability_date=payload.availability_date,
        weekday=derive_weekday_name(payload.availability_date),
        start_time=normalized_start,
        end_time=normalized_end,
    )
    db.add(availability)
    await db.commit()
    await db.refresh(availability)
    return availability


@app.get(
    "/teachers/{teacher_id}/availability",
    response_model=list[schemas.AvailabilityOut],
    tags=["Teacher Availability"],
)
async def list_availability(teacher_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.TeacherAvailability)
        .options(selectinload(models.TeacherAvailability.teacher))
        .where(
            models.TeacherAvailability.teacher_id == teacher_id,
            models.TeacherAvailability.deleted_at.is_(None),
        )
    )
    return result.scalars().all()


@app.get(
    "/availability/{availability_id}",
    response_model=schemas.AvailabilityOut,
    tags=["Teacher Availability"],
)
async def get_availability(
    availability_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = await db.execute(
        select(models.TeacherAvailability)
        .options(selectinload(models.TeacherAvailability.teacher))
        .where(
            models.TeacherAvailability.id == availability_id,
            models.TeacherAvailability.deleted_at.is_(None),
        )
    )
    availability = result.scalar_one_or_none()
    if availability is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    if current_user.role not in {models.UserRole.SUPERUSER, models.UserRole.ADMIN} and availability.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view availability")
    return availability


@app.put(
    "/availability/{availability_id}",
    response_model=schemas.AvailabilityOut,
    tags=["Teacher Availability"],
)
async def update_availability(
    availability_id: int,
    payload: schemas.AvailabilityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ensure_teacher(current_user)
    result = await db.execute(
        select(models.TeacherAvailability)
        .options(selectinload(models.TeacherAvailability.teacher))
        .where(
            models.TeacherAvailability.id == availability_id,
            models.TeacherAvailability.deleted_at.is_(None),
        )
    )
    availability = result.scalar_one_or_none()
    if availability is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    if current_user.role not in {models.UserRole.SUPERUSER, models.UserRole.ADMIN} and availability.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update availability")

    availability_date = payload.availability_date or availability.availability_date
    start_time = (
        ensure_time_with_timezone(payload.start_time)
        if payload.start_time is not None
        else availability.start_time
    )
    end_time = (
        ensure_time_with_timezone(payload.end_time)
        if payload.end_time is not None
        else availability.end_time
    )

    if start_time >= end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be later than start time",
        )

    await assert_no_overlapping_slots(
        db=db,
        teacher_id=availability.teacher_id,
        availability_date=availability_date,
        start_time=start_time,
        end_time=end_time,
        exclude_id=availability.id,
    )

    if payload.availability_date is not None:
        availability.availability_date = payload.availability_date
        availability.weekday = derive_weekday_name(payload.availability_date)
    if payload.start_time is not None:
        availability.start_time = start_time
    if payload.end_time is not None:
        availability.end_time = end_time
    if payload.is_booked is not None:
        availability.is_booked = payload.is_booked

    await db.commit()
    await db.refresh(availability)
    return availability


@app.delete(
    "/availability/{availability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Teacher Availability"],
)
async def delete_availability(
    availability_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ensure_teacher(current_user)
    result = await db.execute(
        select(models.TeacherAvailability).where(
            models.TeacherAvailability.id == availability_id,
            models.TeacherAvailability.deleted_at.is_(None),
        )
    )
    availability = result.scalar_one_or_none()
    if availability is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    if current_user.role not in {models.UserRole.SUPERUSER, models.UserRole.ADMIN} and availability.teacher_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete availability")

    availability.deleted_at = models.now_in_utc_plus_8()
    await db.commit()
    return None


@app.post("/bookings", response_model=schemas.BookingOut, tags=["Bookings"])
async def book_availability(
    payload: schemas.BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ensure_student(current_user)
    google_event: models.GoogleCalendarEvent | None = None

    student_id = payload.student_id or current_user.id
    if payload.student_id and current_user.role not in {models.UserRole.ADMIN, models.UserRole.SUPERUSER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to book for another student")

    student_result = await db.execute(
        select(models.User).where(models.User.id == student_id, models.User.deleted_at.is_(None))
    )
    booking_student = student_result.scalar_one_or_none()
    if booking_student is None or booking_student.role != models.UserRole.STUDENT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student not found")
    if current_user.role in {models.UserRole.ADMIN, models.UserRole.SUPERUSER} and payload.student_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="student_id is required for admin booking")

    try:
        availability_result = await db.execute(
            select(models.TeacherAvailability)
            .options(selectinload(models.TeacherAvailability.teacher))
            .where(
                models.TeacherAvailability.id == payload.availability_id,
                models.TeacherAvailability.deleted_at.is_(None),
            )
        )
        availability = availability_result.scalar_one_or_none()
        if availability is None or availability.is_booked:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found or already booked")

        teacher_result = await db.execute(
            select(models.User).where(
                models.User.id == availability.teacher_id,
                models.User.deleted_at.is_(None),
            )
        )
        teacher = teacher_result.scalar_one_or_none()
        if teacher is None:
            logger.error(
                "Teacher %s unavailable for availability %s", availability.teacher_id, availability.id
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Teacher unavailable")

        platform_domain_map = {
            "Google Meet": "meet.google.com",
            "Zoom": "zoom.us",
            "VOOM": "voom.com",
        }
        platform_domain = platform_domain_map.get(payload.platform, "voom.com")
        now_ts = int(datetime.now(tz=models.UTC_PLUS_8).timestamp())
        fallback_link = f"https://{platform_domain}/{teacher.id}-{booking_student.id}-{now_ts}"

        availability.is_booked = 1

        booking = models.LessonBooking(
            availability_id=availability.id,
            student_id=booking_student.id,
            teacher_id=teacher.id,
            platform=payload.platform,
            conference_link=fallback_link,
        )
        db.add(booking)
        await db.flush()

        start_dt, end_dt = combine_availability_window(availability)
        duration_minutes = max(1, int((end_dt - start_dt).total_seconds() // 60))

        if payload.platform == "Google Meet":
            try:
                google_event = await google_integration.create_calendar_event_for_booking(
                    db=db,
                    booking=booking,
                    availability=availability,
                    teacher=teacher,
                    student=booking_student,
                    reserved_by_email=current_user.email,
                )
            except google_integration.GoogleIntegrationError as exc:
                await db.rollback()
                logger.error(
                    "Failed to generate Google Meet link for booking %s: %s", booking.id, exc
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to generate Google Meet link",
                ) from exc

            if not google_event.meet_link:
                await db.rollback()
                logger.error("Google Meet link missing for booking %s", booking.id)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Google Meet link was not generated",
                )

            booking.conference_link = google_event.meet_link
            booking.platform = "Google Meet"

        elif payload.platform in {"Zoom", "VOOM"}:
            try:
                zoom_meeting = await asyncio.to_thread(
                    zoom_integration.create_zoom_meeting,
                    start_time=start_dt,
                    duration_minutes=duration_minutes,
                    topic=f"Lesson: {current_user.full_name} ↔ {teacher.full_name}",
                )
            except zoom_integration.ZoomIntegrationError as exc:
                await db.rollback()
                logger.error("Failed to create Zoom meeting for booking %s: %s", booking.id, exc)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to generate Zoom meeting",
                ) from exc

            booking.conference_link = zoom_meeting["join_url"]
            booking.platform = "Zoom"
            zoom_record = models.ZoomRecording(
                booking_id=booking.id,
                meeting_id=str(zoom_meeting["id"]),
                start_url=zoom_meeting.get("start_url"),
                join_url=zoom_meeting.get("join_url"),
            )
            db.add(zoom_record)
            zoom_description_lines = [
                f"Zoom Meeting ID: {zoom_meeting['id']}",
                f"Host Start URL: {zoom_meeting['start_url']}",
                f"Join URL: {zoom_meeting['join_url']}",
            ]

            try:
                google_event = await google_integration.create_calendar_event_for_booking(
                    db=db,
                    booking=booking,
                    availability=availability,
                    teacher=teacher,
                    student=booking_student,
                    reserved_by_email=current_user.email,
                    conference_solution_type=None,
                    extra_description_lines=zoom_description_lines,
                )
            except google_integration.GoogleIntegrationError as exc:
                await db.rollback()
                logger.error(
                    "Failed to create Google Calendar event for Zoom booking %s: %s",
                    booking.id,
                    exc,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to create Google Calendar event",
                ) from exc

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
    except Exception:
        await db.rollback()
        raise

    if google_event:
        await db.refresh(google_event)

    await db.refresh(booking)
    await db.refresh(
        booking, attribute_names=["availability", "student", "teacher", "zoom_recording"]
    )
    return booking


@app.get("/bookings/{booking_id}", response_model=schemas.BookingOut, tags=["Bookings"])
async def get_booking(
    booking_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await get_booking_with_permission(booking_id, current_user, db)
    return booking


@app.put("/bookings/{booking_id}", response_model=schemas.BookingOut, tags=["Bookings"])
async def update_booking(
    booking_id: int,
    payload: schemas.BookingUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await get_booking_with_permission(booking_id, current_user, db)

    if payload.platform is not None:
        booking.platform = payload.platform
    if payload.conference_link is not None:
        booking.conference_link = payload.conference_link

    await db.commit()
    await db.refresh(booking)
    return booking


@app.delete("/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Bookings"])
async def delete_booking(
    booking_id: int,
    payload: schemas.BookingCancel | None = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        booking = await get_booking_with_permission(booking_id, current_user, db)

        if booking.availability_id:
            availability_result = await db.execute(
                select(models.TeacherAvailability).where(models.TeacherAvailability.id == booking.availability_id)
            )
            availability = availability_result.scalar_one_or_none()
            if availability:
                availability.is_booked = 0

        event_result = await db.execute(
            select(models.GoogleCalendarEvent).where(
                models.GoogleCalendarEvent.booking_id == booking.id,
                models.GoogleCalendarEvent.deleted_at.is_(None),
            )
        )
        calendar_event = event_result.scalar_one_or_none()
        if calendar_event:
            try:
                await google_integration.delete_calendar_event(calendar_event)
            except google_integration.GoogleIntegrationError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to cancel Google Calendar event",
                ) from exc

            calendar_event.deleted_at = models.now_in_utc_plus_8()

        if current_user.role == models.UserRole.TEACHER:
            default_reason = "教師取消"
        elif current_user.role in {models.UserRole.SUPERUSER, models.UserRole.ADMIN}:
            default_reason = "管理員取消"
        else:
            default_reason = "學生取消"
        booking.status = models.LessonBooking.BookingStatus.CANCELLED
        booking.status_desc = (payload.status_desc if payload else None) or default_reason
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return None


@app.post("/orders", response_model=schemas.OrderOut, tags=["Orders"])
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


@app.get("/orders", response_model=list[schemas.OrderOut], tags=["Orders"])
async def list_orders(
    db: AsyncSession = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)
):
    ensure_student(current_user)
    if current_user.role == models.UserRole.SUPERUSER:
        result = await db.execute(select(models.Order).where(models.Order.deleted_at.is_(None)))
    else:
        result = await db.execute(
            select(models.Order).where(
                models.Order.student_id == current_user.id, models.Order.deleted_at.is_(None)
            )
        )
    return result.scalars().all()


@app.get("/orders/{order_id}", response_model=schemas.OrderOut, tags=["Orders"])
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = await get_order_with_permission(order_id, current_user, db)
    return order


@app.put("/orders/{order_id}", response_model=schemas.OrderOut, tags=["Orders"])
async def update_order(
    order_id: int,
    payload: schemas.OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = await get_order_with_permission(order_id, current_user, db)

    if payload.order_total is not None:
        order.order_total = payload.order_total
    if payload.lesson_credits is not None:
        order.lesson_credits = payload.lesson_credits
    if payload.coupon_code is not None:
        order.coupon_code = payload.coupon_code

    await db.commit()
    await db.refresh(order)
    return order


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Orders"])
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = await get_order_with_permission(order_id, current_user, db)
    order.deleted_at = models.now_in_utc_plus_8()
    await db.commit()
    return None


@app.get("/bookings", response_model=list[schemas.BookingOut], tags=["Bookings"])
async def list_bookings(
    current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)
):
    base_query = (
        select(models.LessonBooking)
        .options(
            selectinload(models.LessonBooking.availability).selectinload(
                models.TeacherAvailability.teacher
            ),
            selectinload(models.LessonBooking.student),
            selectinload(models.LessonBooking.teacher),
            selectinload(models.LessonBooking.zoom_recording),
        )
        .where(models.LessonBooking.deleted_at.is_(None))
    )
    if current_user.role in {models.UserRole.SUPERUSER, models.UserRole.ADMIN}:
        result = await db.execute(base_query)
    elif current_user.role == models.UserRole.TEACHER:
        result = await db.execute(
            base_query.where(models.LessonBooking.teacher_id == current_user.id)
        )
    else:
        result = await db.execute(
            base_query.where(models.LessonBooking.student_id == current_user.id)
        )
    return result.scalars().all()


@app.post(
    "/bookings/{booking_id}/zoom-recording",
    response_model=schemas.ZoomRecordingOut,
    tags=["Zoom"],
)
async def upload_zoom_recording(
    booking_id: int,
    payload: schemas.ZoomRecordingRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    booking = await get_booking_with_permission(booking_id, current_user, db)
    if booking.platform != "Zoom":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recording upload is only available for Zoom bookings",
        )

    result = await db.execute(
        select(models.ZoomRecording).where(models.ZoomRecording.booking_id == booking.id)
    )
    zoom_record = result.scalar_one_or_none()

    meeting_id = payload.meeting_id or (zoom_record.meeting_id if zoom_record else None)
    if not meeting_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meeting ID is required")

    if zoom_record is None:
        zoom_record = models.ZoomRecording(
            booking_id=booking.id,
            meeting_id=meeting_id,
            join_url=booking.conference_link,
        )
        db.add(zoom_record)
    else:
        zoom_record.meeting_id = meeting_id

    try:
        recording = await asyncio.to_thread(
            zoom_integration.download_meeting_recording, meeting_id
        )
    except zoom_integration.ZoomIntegrationError as exc:
        logger.error("Failed to fetch Zoom recording for meeting %s: %s", meeting_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch Zoom recording",
        ) from exc

    try:
        upload_result = await google_integration.upload_file_to_drive(
            file_name=recording["file_name"],
            mime_type=recording["mime_type"],
            content=recording["content"],
            share_email=payload.share_email,
            folder_id=os.getenv("GOOGLE_DRIVE_RECORDING_FOLDER_ID"),
        )
    except google_integration.GoogleIntegrationError as exc:
        logger.error(
            "Failed to upload Zoom recording %s to Drive for booking %s: %s",
            meeting_id,
            booking.id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to upload recording to Google Drive",
        ) from exc

    try:
        await asyncio.to_thread(zoom_integration.delete_meeting_recordings, meeting_id)
    except zoom_integration.ZoomIntegrationError as exc:
        logger.error("Failed to delete Zoom recordings for meeting %s: %s", meeting_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to delete Zoom recording",
        ) from exc

    logger.info(
        "Uploaded Zoom recording for meeting %s to Drive file %s shared with %s",
        meeting_id,
        upload_result.get("id"),
        payload.share_email,
    )

    zoom_record.recording_download_url = recording.get("download_url")
    zoom_record.file_name = recording.get("file_name")
    zoom_record.drive_file_id = upload_result.get("id")
    zoom_record.drive_share_link = upload_result.get("webViewLink") or upload_result.get(
        "webContentLink"
    )
    zoom_record.shared_with_email = payload.share_email

    await db.commit()
    await db.refresh(zoom_record)
    return zoom_record


@app.get(
    "/meeting-records",
    response_model=list[schemas.MeetingRecordOut],
    tags=["Meeting Records"],
)
async def list_meeting_records(
    current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)
):
    query = select(models.MeetingRecord).join(
        models.LessonBooking, models.MeetingRecord.booking_id == models.LessonBooking.id
    )
    query = query.where(models.MeetingRecord.deleted_at.is_(None))
    if current_user.role not in {models.UserRole.SUPERUSER, models.UserRole.ADMIN}:
        query = query.where(
            or_(
                models.LessonBooking.teacher_id == current_user.id,
                models.LessonBooking.student_id == current_user.id,
            )
        )
    result = await db.execute(query)
    return result.scalars().all()


@app.post(
    "/meeting-records",
    response_model=schemas.MeetingRecordOut,
    tags=["Meeting Records"],
)
async def create_meeting_record(
    payload: schemas.MeetingRecordCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_booking_with_permission(payload.booking_id, current_user, db)

    record = models.MeetingRecord(
        booking_id=payload.booking_id,
        reserved_by_id=payload.reserved_by_id or current_user.id,
        platform=payload.platform,
        conference_link=payload.conference_link,
        start_at=normalize_to_utc_plus_8(payload.start_at),
        end_at=normalize_to_utc_plus_8(payload.end_at),
        teacher_email=payload.teacher_email,
        student_email=payload.student_email,
        participant_emails=payload.participant_emails,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@app.get(
    "/meeting-records/{record_id}",
    response_model=schemas.MeetingRecordOut,
    tags=["Meeting Records"],
)
async def get_meeting_record(
    record_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.MeetingRecord).where(
            models.MeetingRecord.id == record_id, models.MeetingRecord.deleted_at.is_(None)
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting record not found")
    await get_booking_with_permission(record.booking_id, current_user, db)
    return record


@app.put(
    "/meeting-records/{record_id}",
    response_model=schemas.MeetingRecordOut,
    tags=["Meeting Records"],
)
async def update_meeting_record(
    record_id: int,
    payload: schemas.MeetingRecordUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.MeetingRecord).where(
            models.MeetingRecord.id == record_id, models.MeetingRecord.deleted_at.is_(None)
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting record not found")
    await get_booking_with_permission(record.booking_id, current_user, db)

    if payload.reserved_by_id is not None:
        record.reserved_by_id = payload.reserved_by_id
    if payload.platform is not None:
        record.platform = payload.platform
    if payload.conference_link is not None:
        record.conference_link = payload.conference_link
    if payload.start_at is not None:
        record.start_at = normalize_to_utc_plus_8(payload.start_at)
    if payload.end_at is not None:
        record.end_at = normalize_to_utc_plus_8(payload.end_at)
    if payload.teacher_email is not None:
        record.teacher_email = payload.teacher_email
    if payload.student_email is not None:
        record.student_email = payload.student_email
    if payload.participant_emails is not None:
        record.participant_emails = payload.participant_emails

    await db.commit()
    await db.refresh(record)
    return record


@app.delete(
    "/meeting-records/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Meeting Records"],
)
async def delete_meeting_record(
    record_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.MeetingRecord).where(
            models.MeetingRecord.id == record_id, models.MeetingRecord.deleted_at.is_(None)
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting record not found")
    await get_booking_with_permission(record.booking_id, current_user, db)

    record.deleted_at = models.now_in_utc_plus_8()
    await db.commit()
    return None


@app.get(
    "/calendar-events",
    response_model=list[schemas.CalendarEventOut],
    tags=["Calendar Events"],
)
async def list_calendar_events(
    current_user: models.User = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)
):
    query = select(models.GoogleCalendarEvent).join(
        models.LessonBooking, models.GoogleCalendarEvent.booking_id == models.LessonBooking.id
    ).where(models.GoogleCalendarEvent.deleted_at.is_(None))
    if current_user.role not in {models.UserRole.SUPERUSER, models.UserRole.ADMIN}:
        query = query.where(
            or_(
                models.LessonBooking.teacher_id == current_user.id,
                models.LessonBooking.student_id == current_user.id,
            )
        )
    result = await db.execute(query)
    return result.scalars().all()


@app.post(
    "/calendar-events",
    response_model=schemas.CalendarEventOut,
    tags=["Calendar Events"],
)
async def create_calendar_event(
    payload: schemas.CalendarEventCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await get_booking_with_permission(payload.booking_id, current_user, db)

    event = models.GoogleCalendarEvent(
        booking_id=payload.booking_id,
        calendar_event_id=payload.calendar_event_id,
        calendar_id=payload.calendar_id or "primary",
        summary=payload.summary,
        description=payload.description,
        meet_link=payload.meet_link,
        start_at=normalize_to_utc_plus_8(payload.start_at),
        end_at=normalize_to_utc_plus_8(payload.end_at),
        creator_email=payload.creator_email,
        attendee_emails=payload.attendee_emails,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@app.get(
    "/calendar-events/{event_id}",
    response_model=schemas.CalendarEventOut,
    tags=["Calendar Events"],
)
async def get_calendar_event(
    event_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.GoogleCalendarEvent).where(
            models.GoogleCalendarEvent.id == event_id,
            models.GoogleCalendarEvent.deleted_at.is_(None),
        )
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found")
    await get_booking_with_permission(event.booking_id, current_user, db)
    return event


@app.put(
    "/calendar-events/{event_id}",
    response_model=schemas.CalendarEventOut,
    tags=["Calendar Events"],
)
async def update_calendar_event(
    event_id: int,
    payload: schemas.CalendarEventUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.GoogleCalendarEvent).where(
            models.GoogleCalendarEvent.id == event_id,
            models.GoogleCalendarEvent.deleted_at.is_(None),
        )
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found")
    await get_booking_with_permission(event.booking_id, current_user, db)

    if payload.calendar_event_id is not None:
        event.calendar_event_id = payload.calendar_event_id
    if payload.calendar_id is not None:
        event.calendar_id = payload.calendar_id
    if payload.summary is not None:
        event.summary = payload.summary
    if payload.description is not None:
        event.description = payload.description
    if payload.meet_link is not None:
        event.meet_link = payload.meet_link
    if payload.start_at is not None:
        event.start_at = normalize_to_utc_plus_8(payload.start_at)
    if payload.end_at is not None:
        event.end_at = normalize_to_utc_plus_8(payload.end_at)
    if payload.creator_email is not None:
        event.creator_email = payload.creator_email
    if payload.attendee_emails is not None:
        event.attendee_emails = payload.attendee_emails

    await db.commit()
    await db.refresh(event)
    return event


@app.delete(
    "/calendar-events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Calendar Events"],
)
async def delete_calendar_event(
    event_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.GoogleCalendarEvent).where(
            models.GoogleCalendarEvent.id == event_id,
            models.GoogleCalendarEvent.deleted_at.is_(None),
        )
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar event not found")
    await get_booking_with_permission(event.booking_id, current_user, db)

    event.deleted_at = models.now_in_utc_plus_8()
    await db.commit()
    return None
