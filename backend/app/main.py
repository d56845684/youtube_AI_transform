from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import auth, google_integration, models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Language Tutor Marketplace")

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
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = auth.get_password_hash(user_in.password)
    user = models.User(
        email=user_in.email,
        full_name=user_in.full_name,
        role=models.UserRole(user_in.role.value),
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth.create_access_token({"sub": str(user.id), "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/teachers/availability", response_model=schemas.AvailabilityOut)
def create_availability(
    payload: schemas.AvailabilityCreate,
    db: Session = Depends(get_db),
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
    db.commit()
    db.refresh(availability)
    return availability


@app.get("/teachers/{teacher_id}/availability", response_model=list[schemas.AvailabilityOut])
def list_availability(teacher_id: int, db: Session = Depends(get_db)):
    return db.query(models.TeacherAvailability).filter(models.TeacherAvailability.teacher_id == teacher_id).all()


@app.post("/bookings", response_model=schemas.BookingOut)
def book_availability(
    payload: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    ensure_student(current_user)
    availability = db.query(models.TeacherAvailability).filter(models.TeacherAvailability.id == payload.availability_id).first()
    if availability is None or availability.is_booked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found or already booked")

    teacher = db.query(models.User).filter(models.User.id == availability.teacher_id).first()
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
    db.commit()
    db.refresh(booking)

    try:
        google_integration.sync_booking_to_google(
            booking=booking,
            availability=availability,
            teacher=teacher,
            student=current_user,
        )
    except google_integration.GoogleIntegrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    return booking


@app.post("/orders", response_model=schemas.OrderOut)
def create_order(
    payload: schemas.OrderCreate,
    db: Session = Depends(get_db),
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
    db.commit()
    db.refresh(order)
    return order


@app.get("/bookings", response_model=list[schemas.BookingOut])
def list_bookings(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if current_user.role == models.UserRole.TEACHER:
        return db.query(models.LessonBooking).filter(models.LessonBooking.teacher_id == current_user.id).all()
    return db.query(models.LessonBooking).filter(models.LessonBooking.student_id == current_user.id).all()
