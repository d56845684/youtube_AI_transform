FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1
ENV DATABASE_URL=postgresql+asyncpg://user:password@db:5432/language_tutor
ENV SECRET_KEY=change-me

ENTRYPOINT ["/entrypoint.sh"]
