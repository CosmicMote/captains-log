# ── Stage 1: Build the React frontend ────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /build
COPY frontend/package*.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
# The app uses /api as a relative (base-aware) path, so no VITE_API_BASE needed at build time
RUN npm run build


# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim

# Install nginx
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./

# Copy built frontend from Stage 1
COPY --from=frontend-builder /build/dist /app/frontend
# Keep index.html as a template; start.sh renders it with the runtime BASE_PATH
RUN mv /app/frontend/index.html /app/index.html.template

# nginx config
COPY docker/nginx.conf /etc/nginx/sites-enabled/default

# Startup script
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

# /data holds journal.db and auth_config.json — mount a volume here
VOLUME /data
ENV JOURNAL_DATA_DIR=/data

# Optional sub-path to serve the app from behind a reverse proxy, e.g.
# docker run -e BASE_PATH=/captains-log for https://host/captains-log/.
# Defaults to the root.
ENV BASE_PATH=""

# Number of Dropbox backups to keep; older ones are deleted after each backup.
ENV MAX_BACKUPS=5

EXPOSE 80

CMD ["/start.sh"]
