# Captain's Log

A personal journal application with a Star Trek: The Next Generation theme. Write dated journal entries, navigate through your history with a calendar, and import existing journals from RedNotebook.

## Features

- Write and edit journal entries by date
- Calendar sidebar with dot indicators on days that have entries
- Previous/next navigation between entries
- Stardate displayed alongside each entry date
- Dark mode with a CSS starfield and nebula effects
- Password-protected access
- HTTPS support (self-signed or real certificate)
- Import tool for RedNotebook journals

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, Vite, react-calendar

## Setup

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

The frontend reads the backend URL from `frontend/.env`. Copy the example file to get started:

```bash
cp .env.example .env
```

## HTTPS

### Option A — Self-signed certificate (development)

```bash
cd backend
python generate_cert.py
python start.py
```

The certificate is saved to `backend/certs/` and the paths are stored in `auth_config.json`
so `start.py` enables HTTPS automatically from then on.

Your browser will show a security warning on first visit. To silence it, add `backend/certs/cert.pem`
to your system's trusted certificate store.

When using HTTPS, update `frontend/.env` to match:

```
VITE_API_BASE=https://localhost:8000
```

Also update the CORS origin in `backend/main.py` if the frontend URL changes.

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
