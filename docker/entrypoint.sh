#!/bin/sh
set -e
cd /app/backend
uvicorn main:app --host 127.0.0.1 --port 8000 &
sleep 2
exec nginx -g "daemon off;"
