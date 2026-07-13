import sqlite3
import os

# Detect if the app is running on Render
IS_RENDER = os.getenv("RENDER") is not None

if IS_RENDER:
    DB_PATH = "/tmp/jobs.db"
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn   = get_connection()
    cursor = conn.cursor()

    # Jobs table — same as before
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id       TEXT UNIQUE,
            title        TEXT,
            company      TEXT,
            location     TEXT,
            source       TEXT,
            link         TEXT,
            score        INTEGER,
            verdict      TEXT,
            reason       TEXT,
            user_email   TEXT,
            status       TEXT DEFAULT 'seen',
            seen_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Run history table — NEW
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email   TEXT,
            query        TEXT,
            location     TEXT,
            jobs_found   INTEGER,
            jobs_new     INTEGER,
            jobs_skipped INTEGER,
            ran_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def is_job_seen(job_id: str, user_email: str) -> bool:
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM jobs WHERE job_id = ? AND user_email = ?",
        (job_id, user_email)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_job(job: dict, user_email: str):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO jobs
        (job_id, title, company, location, source, link, score, verdict, reason, user_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.get("job_id"),
        job.get("title"),
        job.get("company"),
        job.get("location"),
        job.get("source"),
        job.get("link"),
        job.get("score"),
        job.get("verdict"),
        job.get("reason"),
        user_email
    ))
    conn.commit()
    conn.close()

def get_all_jobs(user_email: str, min_score: int = 0) -> list[dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM jobs
        WHERE user_email = ? AND score >= ?
        ORDER BY seen_at DESC
    """, (user_email, min_score))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_job_status(job_id: str, status: str):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE jobs SET status = ? WHERE job_id = ?",
        (status, job_id)
    )
    conn.commit()
    conn.close()

def save_run(user_email: str, query: str, location: str,
             jobs_found: int, jobs_new: int, jobs_skipped: int):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO runs (user_email, query, location, jobs_found, jobs_new, jobs_skipped)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_email, query, location, jobs_found, jobs_new, jobs_skipped))
    conn.commit()
    conn.close()