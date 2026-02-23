"""
Database Manager
================
SQLite CRUD for job listings.

Changes vs original:
  • Added `source` column (tracks which API/scraper the job came from)
  • Added `insert_job_safe()` — deduplicates on (title, company, location)
    before inserting; use this instead of insert_job() everywhere
  • insert_job() kept for backward compatibility but now calls insert_job_safe()
  • _migrate() adds missing columns AND the index after columns are guaranteed present
    (fixes OperationalError: no such column: dedup_hash on existing databases)
"""

import hashlib
import sqlite3
import os

try:
    from config.constants import get_project_root
    _root = get_project_root()
except ImportError:
    _root = os.getcwd()

DB_DIR = os.path.join(_root, "data")
DB_PATH = os.path.join(DB_DIR, "jobs.db")


class DatabaseManager:

    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute("PRAGMA journal_mode=WAL")   # safer for threaded writes
        self.create_table()
        self._migrate()   # always runs after create_table

    # ── schema ─────────────────────────────────────────────────────────────────

    def create_table(self):
        """
        Creates the jobs table for brand-new databases.
        NOTE: The dedup index is created in _migrate() — NOT here —
        so that existing databases that don't have the dedup_hash column yet
        don't throw 'no such column' when the index is created.
        """
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                title        TEXT,
                company      TEXT,
                location     TEXT,
                salary       INTEGER,
                experience   TEXT,
                skills       TEXT,
                job_type     TEXT,
                posted_date  TEXT,
                source       TEXT DEFAULT 'unknown',
                dedup_hash   TEXT
            )
        """)
        self.conn.commit()

    def _migrate(self):
        """
        Safe migration for existing databases:
          1. Add missing columns (source, dedup_hash) if not present.
          2. THEN create the index (column is now guaranteed to exist).
          3. Backfill random hashes for legacy rows that have no hash yet.
        """
        cursor = self.conn.execute("PRAGMA table_info(jobs)")
        existing = {row[1] for row in cursor.fetchall()}

        # Step 1 — add missing columns
        migrations = {
            "source":     "ALTER TABLE jobs ADD COLUMN source TEXT DEFAULT 'unknown'",
            "dedup_hash": "ALTER TABLE jobs ADD COLUMN dedup_hash TEXT",
        }
        for col, sql in migrations.items():
            if col not in existing:
                self.conn.execute(sql)
        self.conn.commit()

        # Step 2 — create index AFTER column is guaranteed to exist
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dedup
            ON jobs (dedup_hash)
        """)
        self.conn.commit()

        # Step 3 — backfill unique random hashes for pre-existing rows
        self.conn.execute("""
            UPDATE jobs
            SET dedup_hash = lower(hex(randomblob(8)))
            WHERE dedup_hash IS NULL OR dedup_hash = ''
        """)
        self.conn.commit()

    # ── insert ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _make_hash(title: str, company: str, location: str) -> str:
        key = (
            f"{str(title).lower().strip()}"
            f"|{str(company).lower().strip()}"
            f"|{str(location).lower().strip()}"
        )
        return hashlib.sha1(key.encode()).hexdigest()

    def insert_job_safe(self, job: tuple, source: str = "unknown") -> bool:
        """
        Insert a job only if (title, company, location) hasn't been seen before.

        Parameters
        ----------
        job : tuple
            (title, company, location, salary, experience, skills, job_type, posted_date)
        source : str
            Origin API label: 'remoteok', 'remotive', 'adzuna', 'indeed'

        Returns
        -------
        bool
            True if inserted, False if duplicate was skipped.
        """
        if len(job) < 8:
            return False

        title, company, location = str(job[0]), str(job[1]), str(job[2])
        dedup_hash = self._make_hash(title, company, location)

        # skip if duplicate
        cur = self.conn.execute(
            "SELECT id FROM jobs WHERE dedup_hash = ? LIMIT 1", (dedup_hash,)
        )
        if cur.fetchone():
            return False

        self.conn.execute(
            """
            INSERT INTO jobs
                (title, company, location, salary, experience,
                 skills, job_type, posted_date, source, dedup_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (*job[:8], source, dedup_hash),
        )
        self.conn.commit()
        return True

    def insert_job(self, job: tuple, source: str = "unknown"):
        """Backward-compatible insert — delegates to insert_job_safe."""
        self.insert_job_safe(job, source=source)

    # ── read ───────────────────────────────────────────────────────────────────

    def fetch_all_jobs(self) -> list:
        cursor = self.conn.execute(
            "SELECT id, title, company, location, salary, experience, "
            "skills, job_type, posted_date FROM jobs"
        )
        return cursor.fetchall()

    def fetch_jobs_by_source(self, source: str) -> list:
        cursor = self.conn.execute(
            "SELECT id, title, company, location, salary, experience, "
            "skills, job_type, posted_date FROM jobs WHERE source = ?",
            (source,),
        )
        return cursor.fetchall()

    def get_source_counts(self) -> dict:
        """Return {source: job_count} — useful for the status bar."""
        cursor = self.conn.execute(
            "SELECT source, COUNT(*) FROM jobs GROUP BY source ORDER BY COUNT(*) DESC"
        )
        return dict(cursor.fetchall())

    def count_jobs(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

    # ── delete ─────────────────────────────────────────────────────────────────

    def clear_jobs(self):
        self.conn.execute("DELETE FROM jobs")
        self.conn.commit()

    def clear_by_source(self, source: str):
        self.conn.execute("DELETE FROM jobs WHERE source = ?", (source,))
        self.conn.commit()