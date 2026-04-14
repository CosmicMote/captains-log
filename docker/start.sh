#!/bin/sh
set -e

# Ensure the data directory exists (in case the volume wasn't pre-created)
mkdir -p /data

# Start uvicorn in the background
cd /app/backend
uvicorn main:app --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

# Give uvicorn a moment to start before nginx begins proxying
sleep 1

echo "Captain's Log is running at http://localhost:80"
echo "Run 'docker exec -it <container> python /app/backend/setup_password.py' to set a password."

# Start nginx in the foreground (keeps the container alive)
# If nginx exits, also stop uvicorn
trap "kill $UVICORN_PID 2>/dev/null" EXIT
nginx -g 'daemon off;'
