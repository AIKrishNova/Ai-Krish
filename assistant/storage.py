"""Local notes storage using SQLite (built into Python)."""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


def _now():
    return datetime.now().isoformat(timespec="seconds")


class NoteStore:
    def __init__(self, path):
        self.path = str(path)
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(SCHEMA)

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def add(self, body, title=None):
        body = (body or "").strip()
        if not body:
            raise ValueError("A note cannot be empty.")
        title = (title or body.splitlines()[0])[:50]
        with closing(self._connect()) as conn:
            with conn:
                cur = conn.execute(
                    "INSERT INTO notes (title, body, created_at) VALUES (?, ?, ?)",
                    (title, body, _now()),
                )
                return cur.lastrowid

    def get(self, note_id):
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return dict(row) if row else None

    def latest(self):
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM notes ORDER BY id DESC LIMIT 1").fetchone()
        return dict(row) if row else None

    def list(self, limit=20):
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM notes ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def search(self, term, limit=20):
        safe = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = "%" + safe + "%"
        sql = (
            "SELECT * FROM notes WHERE title LIKE ? ESCAPE '\\' "
            "OR body LIKE ? ESCAPE '\\' ORDER BY id DESC LIMIT ?"
        )
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, (like, like, limit)).fetchall()
        return [dict(r) for r in rows]

    def delete(self, note_id):
        with closing(self._connect()) as conn:
            with conn:
                cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                return cur.rowcount > 0

    def export_markdown(self, folder):
        """Write all notes to a new .md file. Never overwrites an existing file."""
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM notes ORDER BY id").fetchall()
        if not rows:
            return None, 0
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        name = "notes-" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".md"
        path = folder / name
        with open(path, "x", encoding="utf-8") as handle:  # "x" = fail if it exists
            handle.write("# AI Krish notes\n\n")
            for row in rows:
                handle.write("## #%d %s\n" % (row["id"], row["title"]))
                handle.write("*%s*\n\n%s\n\n" % (row["created_at"], row["body"]))
        return path, len(rows)
