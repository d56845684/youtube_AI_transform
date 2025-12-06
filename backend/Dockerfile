FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql+psycopg2://user:password@db:5432/language_tutor
ENV SECRET_KEY=change-me

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
