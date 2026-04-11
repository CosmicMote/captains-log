#!/usr/bin/env python3
"""Import RedNotebook journal entries into the personal journal SQLite database.

Usage:
    python import_rednotebook.py <path/to/journal.db> <path/to/.rednotebook>
"""

import sys
import sqlite3
import yaml
from pathlib import Path
from datetime import date


def parse_month_file(filepath: Path) -> dict[int, str]:
    """Parse a RedNotebook YYYY-MM.txt file.

    Returns a dict mapping day number (int) to text content (str).
    """
    raw = filepath.read_text(encoding="utf-8")
    if not raw.strip():
        return {}

    parsed = yaml.safe_load(raw)
    if not isinstance(parsed, dict):
        return {}

    result = {}
    for day, data in parsed.items():
        if isinstance(data, dict):
            content = data.get("text") or ""
        else:
            content = str(data) if data else ""
        result[int(day)] = content
    return result


def validate_args(db_path: Path, rb_dir: Path) -> Path:
    """Validate command-line arguments and return the resolved data directory.

    Exits with an error message if any argument is invalid.
    """
    # Validate database path
    if db_path.suffix != ".db":
        print(f"Error: database path must end in .db, got: {db_path}")
        sys.exit(1)
    if not db_path.exists():
        print(f"Error: database not found: {db_path}")
        sys.exit(1)
    if not db_path.is_file():
        print(f"Error: database path is not a file: {db_path}")
        sys.exit(1)

    # Validate RedNotebook path
    if not rb_dir.exists():
        print(f"Error: RedNotebook path not found: {rb_dir}")
        sys.exit(1)
    if not rb_dir.is_dir():
        print(f"Error: RedNotebook path is not a directory: {rb_dir}")
        sys.exit(1)
    if rb_dir.name == ".rednotebook":
        data_dir = rb_dir / "data"
    elif rb_dir.name == "data" and rb_dir.parent.name == ".rednotebook":
        data_dir = rb_dir
    else:
        print(
            f"Error: RedNotebook path must be a .rednotebook directory or "
            f"a data directory inside one, got: {rb_dir}"
        )
        sys.exit(1)
    if not data_dir.is_dir():
        print(f"Error: RedNotebook data directory not found: {data_dir}")
        sys.exit(1)

    return data_dir


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage: python import_rednotebook.py <journal.db> <rednotebook_dir>")
        sys.exit(1)

    db_path = Path(sys.argv[1])
    rb_dir = Path(sys.argv[2])

    data_dir = validate_args(db_path, rb_dir)
    month_files = sorted(data_dir.glob("????-??.txt"))

    if not month_files:
        print(f"Error: no RedNotebook data files (YYYY-MM.txt) found in {data_dir}")
        sys.exit(1)

    print(f"Found {len(month_files)} monthly files in {data_dir}\n")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    total_imported = total_skipped = total_errors = 0

    for filepath in month_files:
        year_str, month_str = filepath.stem.split("-")
        year, month = int(year_str), int(month_str)

        print(f"{filepath.stem}:", end="  ", flush=True)

        try:
            entries = parse_month_file(filepath)
        except Exception as exc:
            print(f"FAILED to parse — {exc}")
            total_errors += 1
            continue

        file_imported = file_skipped = file_errors = 0

        for day in sorted(entries):
            content = entries[day]
            if not content or not content.strip():
                continue

            try:
                entry_date = date(year, month, day).isoformat()
            except ValueError as exc:
                print(f"\n  Invalid date {year}-{month:02d}-{day}: {exc}")
                file_errors += 1
                continue

            try:
                cur.execute(
                    "INSERT OR IGNORE INTO journal_entries (date, content, created_at, updated_at)"
                    " VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                    (entry_date, content),
                )
                if cur.rowcount:
                    file_imported += 1
                else:
                    file_skipped += 1
            except sqlite3.Error as exc:
                print(f"\n  DB error on {entry_date}: {exc}")
                print(f"  Content preview: {content[:120]!r}")
                file_errors += 1

        conn.commit()

        parts = [f"imported {file_imported}"]
        if file_skipped:
            parts.append(f"skipped {file_skipped} (already exist)")
        if file_errors:
            parts.append(f"{file_errors} errors")
        print(", ".join(parts))

        total_imported += file_imported
        total_skipped += file_skipped
        total_errors += file_errors

    conn.close()

    print(f"\n{'─' * 40}")
    print(f"Imported : {total_imported}")
    if total_skipped:
        print(f"Skipped  : {total_skipped}  (entries already in database)")
    if total_errors:
        print(f"Errors   : {total_errors}")
    print("Done.")


if __name__ == "__main__":
    main()
