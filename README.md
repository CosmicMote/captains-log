# Captain's Log

A personal journal application with a Star Trek: The Next Generation theme. Write dated journal entries, navigate through your history with a calendar, and import existing journals from RedNotebook.

## Features

- Write and edit journal entries by date
- Calendar sidebar with dot indicators on days that have entries
- Previous/next navigation between entries
- Stardate displayed alongside each entry date
- Dark mode with a CSS starfield and nebula effects
- Password-protected access
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
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive API docs are at `http://localhost:8000/docs`.

### 2. Frontend

From the `frontend/` directory:

```bash
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## Importing from RedNotebook

Use the import tool from the project root to import entries from an existing RedNotebook journal:

```bash
python import_rednotebook.py <path/to/journal.db> <path/to/.rednotebook>
```

The database path must end in `.db` and the RedNotebook path must be either the `.rednotebook` directory itself or its `data/` subdirectory. Already-imported entries are skipped safely, so re-running the tool is harmless.

Example:

```bash
python import_rednotebook.py backend/journal.db C:\Users\you\.rednotebook
```
