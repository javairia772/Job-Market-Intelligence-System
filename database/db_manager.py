import sqlite3
import os

DB_PATH = os.path.join("data", "jobs.db")


class DatabaseManager:

    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            salary INTEGER,
            experience TEXT,
            skills TEXT,
            job_type TEXT,
            posted_date TEXT
        );
        """
        self.conn.execute(query)
        self.conn.commit()

    def insert_job(self, job):
        query = """
        INSERT INTO jobs 
        (title, company, location, salary, experience, skills, job_type, posted_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, job)
        self.conn.commit()

    def fetch_all_jobs(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM jobs")
        return cursor.fetchall()

    def clear_jobs(self):
        self.conn.execute("DELETE FROM jobs")
        self.conn.commit()