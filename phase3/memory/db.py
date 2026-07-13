import sqlite3
import os

# Database file will be created here automatically
DB_PATH = os.path.join(os.path.dirname(__file__), "jobs.db")

def get_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def init_db():
    """
    Creates the jobs table if it doesn't exist.
    Safe to call multiple times — won't overwrite existing data.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id      TEXT UNIQUE,        -- unique ID from JSearch API
            title       TEXT,
            company     TEXT,
            location    TEXT,
            source      TEXT,
            link        TEXT,
            score       INTEGER,
            verdict     TEXT,
            reason      TEXT,
            status      TEXT DEFAULT 'seen',  -- seen | applied | rejected
            seen_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database ready.")

def is_job_seen(job_id: str) -> bool:
    """Returns True if this job_id already exists in the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,))
    result = cursor.fetchone()

    conn.close()
    return result is not None

def save_job(job: dict):
    """
    Saves a scored job to the database.
    Ignores duplicates silently (INSERT OR IGNORE).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO jobs 
        (job_id, title, company, location, source, link, score, verdict, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.get("job_id"),
        job.get("title"),
        job.get("company"),
        job.get("location"),
        job.get("source"),
        job.get("link"),
        job.get("score"),
        job.get("verdict"),
        job.get("reason")
    ))

    conn.commit()
    conn.close()

def get_all_jobs(min_score: int = 0) -> list[dict]:
    """
    Retrieves all saved jobs, optionally filtered by minimum score.
    Returns newest first.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row  # lets us access columns by name
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM jobs 
        WHERE score >= ?
        ORDER BY seen_at DESC
    """, (min_score,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def update_job_status(job_id: str, status: str):
    """
    Updates the status of a job.
    status can be: 'seen', 'applied', 'rejected'
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE jobs SET status = ? WHERE job_id = ?
    """, (status, job_id))

    conn.commit()
    conn.close()
    print(f"✅ Job {job_id} marked as '{status}'")


if __name__ == "__main__":
    init_db()
    print("All tables created successfully.")