#!/bin/sh
set -e

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
APP_MODULE="${APP_MODULE:-app.main:app}"
RELOAD_FLAG="${UVICORN_RELOAD:-}"

CMD="uvicorn ${APP_MODULE} --host ${HOST} --port ${PORT}"

# Enable reload mode if requested either via environment or explicit flag.
if [ "$RELOAD_FLAG" = "true" ] || [ "$RELOAD_FLAG" = "1" ]; then
  CMD="$CMD --reload"
elif [ "$1" = "--reload" ]; then
  CMD="$CMD --reload"
  shift
fi

exec sh -c "$CMD $*"
