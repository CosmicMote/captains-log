# Captain's Log

A personal journal application with a Star Trek: The Next Generation theme. Write dated journal entries, navigate through your history with a calendar, and import existing journals from RedNotebook.

## Features

- Write and edit journal entries by date
- Auto-save
- Rich text editing with bold, italic, underline, and strikethrough formatting
- Calendar sidebar with dot indicators on days that have entries
- Navigate between entries with previous/next buttons, or jump directly to today
- Stardate displayed alongside each entry date
- Dark mode with a CSS starfield and nebula effects
- Password-protected access
- HTTPS support (self-signed or real certificate)
- Encrypted backup export and import (AES-256-GCM, password-protected `.clog` files)
- Import tool for RedNotebook journals

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, Vite, react-calendar

---

## Running with Docker

### Build the image

From the project root:

```bash
docker build -t captains-log .
```

### Run the container

```bash
docker run --restart unless-stopped -d \
  --name captains-log \
  -p 8080:80 \
  -v captains-log-data:/data \
  captains-log
```

The app will be available at `http://localhost:8080`.

The `/data` volume holds the database and auth config and persists across container restarts.

### Set the password (first-time setup)

```bash
docker exec -it captains-log python /app/backend/setup_password.py
```

### Import a RedNotebook journal into Docker

Copy your RedNotebook data into the container and run the import tool:

```bash
docker cp C:\Users\you\.rednotebook captains-log:/tmp/.rednotebook
docker exec -it captains-log python /app/backend/import_rednotebook.py /data/journal.db /tmp/.rednotebook
```

### HTTPS in Docker

For production use, place a reverse proxy (nginx, Caddy, Traefik) in front of the container to handle TLS termination, and point it at `http://localhost:8080`. This is simpler and more flexible than managing certs inside the container.

---

## Local Development Setup

### 1. Backend

From the `backend/` directory:

```bash
pip install -r requirements.txt
```

Set your login password (first-time setup, or to change it later):

```bash
python setup_password.py
```

Start the development server:

```bash
python start.py
```

The API will be available at `http://localhost:8000` (or `https://` if SSL is configured).  
Interactive API docs are at `http://localhost:8000/docs`.

### 2. Frontend

From the `frontend/` directory:

```bash
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

Copy the env example file to configure the backend URL:

```bash
cp .env.example .env
```

Vite proxies all `/api/*` requests to the backend, so self-signed cert warnings are
handled transparently in dev.

## HTTPS (local development)

### Option A — Self-signed certificate

```bash
cd backend
python generate_cert.py
python start.py
```

The certificate is saved to `backend/certs/` and the paths are stored in `auth_config.json`
so `start.py` enables HTTPS automatically from then on.

Your browser will show a security warning on first visit. To silence it, add `backend/certs/cert.pem`
to your system's trusted certificate store.

Update `frontend/.env` to point Vite's proxy at the HTTPS backend:

```
VITE_API_BASE=https://localhost:8000
```

### Option B — Real certificate (e.g. Let's Encrypt)

```bash
cd backend
python configure_ssl.py /path/to/cert.pem /path/to/key.pem
python start.py
```

### Disabling HTTPS

```bash
cd backend
python configure_ssl.py --clear
python start.py
```

## Importing from RedNotebook

Use the import tool from the project root to import entries from an existing RedNotebook journal:

```bash
python import_rednotebook.py <path/to/journal.db> <path/to/.rednotebook>
```

The database path must end in `.db` and the RedNotebook path must be either the `.rednotebook`
directory itself or its `data/` subdirectory. Already-imported entries are skipped safely,
so re-running the tool is harmless.

Example:

```bash
python import_rednotebook.py backend/journal.db C:\Users\you\.rednotebook
```
