import json, sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/audits.db")

def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                title TEXT,
                participants INTEGER,
                avg_reach INTEGER,
                quality_score INTEGER,
                err_percent REAL,
                warnings TEXT,
                verdict TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audits_username ON audits (username)")
        conn.commit()

def save_audit(data: dict) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO audits
               (username, title, participants, avg_reach, quality_score,
                err_percent, warnings, verdict, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["username"], data.get("title"), data.get("participants"),
                data.get("avg_reach"), data.get("quality_score"),
                data.get("err_percent"),
                json.dumps(data.get("warnings", []), ensure_ascii=False),
                data.get("verdict"),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return cur.lastrowid

def get_previous_audit(username: str, before_id: Optional[int] = None) -> Optional[dict]:
    query = "SELECT * FROM audits WHERE username = ?"
    params: list = [username]
    if before_id is not None:
        query += " AND id < ?"
        params.append(before_id)
    query += " ORDER BY id DESC LIMIT 1"
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(query, params).fetchone()
        if not row:
            return None
        result = dict(row)
        result["warnings"] = json.loads(result["warnings"] or "[]")
        return result

def get_history(username: str, limit: int = 5) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM audits WHERE username = ? ORDER BY id DESC LIMIT ?",
            (username, limit),
        ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["warnings"] = json.loads(item["warnings"] or "[]")
            result.append(item)
        return result
