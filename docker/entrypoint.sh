#!/bin/bash
set -e

# Start gunicorn in background
gunicorn --workers 2 --bind 127.0.0.1:8000 --timeout 120 config.wsgi:application &
GUNICORN_PID=$!

# Wait for gunicorn to be ready
sleep 2

# Start nginx in foreground
nginx -g "daemon off;" &
NGINX_PID=$!

# Handle shutdown
trap "kill $GUNICORN_PID $NGINX_PID 2>/dev/null; exit 0" SIGTERM SIGINT

wait -n
