import sqlite3
from pathlib import Path
from utils.helper import generate_id, now_string


class ProgramService:
    DEFAULT_PROGRAMS = [
        ("PROG_BTECH", "B.Tech", 4, "Bachelor of Technology (4 Years Undergraduate Program)"),
        ("PROG_DEGREE", "Degree", 3, "Undergraduate Degree Program (3 Years)"),
        ("PROG_MTECH", "M.Tech", 2, "Master of Technology (2 Years Postgraduate Program)"),
        ("PROG_MBA", "MBA", 2, "Master of Business Administration (2 Years Postgraduate Program)"),
    ]

    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)
        self._ensure_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        now = now_string()
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS academic_programs (
                    program_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    duration_years INTEGER NOT NULL DEFAULT 4,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cnt = conn.execute("SELECT COUNT(*) FROM academic_programs").fetchone()[0]
            if cnt == 0:
                for prog_id, name, dur, desc in self.DEFAULT_PROGRAMS:
                    conn.execute(
                        "INSERT OR IGNORE INTO academic_programs (program_id, name, duration_years, description, created_at) VALUES (?, ?, ?, ?, ?)",
                        (prog_id, name, dur, desc, now),
                    )

    def list_programs(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM academic_programs ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]

    def get_program(self, program_id_or_name):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM academic_programs WHERE program_id = ? OR LOWER(name) = LOWER(?)",
                (program_id_or_name, program_id_or_name),
            ).fetchone()
            return dict(row) if row else None

    def create_program(self, name: str, duration_years: int = 4, description: str = ""):
        name = (name or "").strip()
        if not name:
            raise ValueError("Program name is required.")
        duration_years = int(duration_years)
        if duration_years < 1 or duration_years > 8:
            raise ValueError("Program duration must be between 1 and 8 years.")

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT program_id FROM academic_programs WHERE LOWER(name) = LOWER(?)",
                (name,),
            ).fetchone()
            if existing:
                raise ValueError(f"Program '{name}' already exists.")

            prog_id = generate_id("PROG")
            now = now_string()
            conn.execute(
                "INSERT INTO academic_programs (program_id, name, duration_years, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (prog_id, name, duration_years, description, now),
            )
            return {
                "program_id": prog_id,
                "name": name,
                "duration_years": duration_years,
                "description": description,
                "created_at": now,
            }

    def delete_program(self, program_id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM academic_programs WHERE program_id = ?", (program_id,))
