# Language Tutor Marketplace

This project demonstrates a three-tier architecture for a real-time language tutoring marketplace. It includes a Python FastAPI backend, a PostgreSQL database, and a static HTML/CSS/JS frontend served via Nginx.

## Features
- Student and teacher roles with JWT authentication and password hashing.
- Students purchase lesson credits (orders) and book available teacher timeslots.
- Teachers publish weekly availability; bookings automatically generate meeting links for Google Meet or VOOM.
- Relational schema with primary and foreign keys linking users, orders, availabilities, and bookings.
- Docker Compose brings up PostgreSQL, the backend API, and the static frontend.

## Running locally
```bash
docker-compose up --build
```
Open the frontend at [http://localhost:8080](http://localhost:8080) and the API at [http://localhost:8000/docs](http://localhost:8000/docs).
Nginx serves the static assets from `frontend/` with a simple health check at [http://localhost:8080/healthz](http://localhost:8080/healthz) to verify the container is reachable.

## Environment
Set environment variables (or copy `.env.example`):
- `DATABASE_URL`: PostgreSQL connection string using the async driver
  (e.g., `postgresql+asyncpg://user:password@db:5432/language_tutor`)
- `SECRET_KEY`: JWT signing key
- `GOOGLE_CREDENTIALS_JSON` or `GOOGLE_CREDENTIALS_FILE`: service account credentials used for Google Sheets and Calendar
  (Sheets/Calendar scopes are required)
- `GOOGLE_SHEETS_ID`: spreadsheet key to log confirmed bookings (optional but recommended)
- `GOOGLE_SHEETS_WORKSHEET`: worksheet/tab name to target; defaults to the first worksheet
- `GOOGLE_CALENDAR_ID`: calendar to receive auto-created lesson events

## API highlights
- `POST /auth/register`: create user (role `student` or `teacher`).
- `POST /auth/token`: OAuth2 password flow for JWT.
- `POST /teachers/availability`: teacher creates availability windows.
- `GET /teachers/{id}/availability`: list availability for a teacher.
- `POST /bookings`: student reserves a slot, generating a conference link.
- `POST /orders`: student buys lesson credits.

The backend schema lives under `backend/app/models.py` and is wired via SQLAlchemy to PostgreSQL.
