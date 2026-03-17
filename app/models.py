"""SQLite database models and helpers for Remote JobFinder."""

import aiosqlite
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "jobs.db")

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    url TEXT NOT NULL,
    description TEXT,
    source TEXT NOT NULL,
    job_type TEXT,
    category TEXT,
    score INTEGER DEFAULT 0,
    posted_at TEXT,
    scraped_at TEXT NOT NULL,
    is_new INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS scrape_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    job_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'success',
    error_message TEXT
);
"""


async def get_db():
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialise the database tables."""
    db = await get_db()
    await db.executescript(CREATE_TABLES)
    await db.commit()
    await db.close()


async def upsert_job(job: dict):
    """Insert or update a job listing."""
    db = await get_db()
    await db.execute(
        """INSERT INTO jobs (id, title, company, location, url, description,
           source, job_type, category, score, posted_at, scraped_at, is_new)
           VALUES (:id, :title, :company, :location, :url, :description,
           :source, :job_type, :category, :score, :posted_at, :scraped_at, 1)
           ON CONFLICT(id) DO UPDATE SET
           title=:title, company=:company, location=:location,
           description=:description, score=:score, scraped_at=:scraped_at,
           is_new=0""",
        job,
    )
    await db.commit()
    await db.close()


async def upsert_jobs(jobs: list[dict]):
    """Insert or update multiple job listings."""
    db = await get_db()
    for job in jobs:
        await db.execute(
            """INSERT INTO jobs (id, title, company, location, url, description,
               source, job_type, category, score, posted_at, scraped_at, is_new)
               VALUES (:id, :title, :company, :location, :url, :description,
               :source, :job_type, :category, :score, :posted_at, :scraped_at, 1)
               ON CONFLICT(id) DO UPDATE SET
               title=:title, company=:company, location=:location,
               description=:description, score=:score, scraped_at=:scraped_at,
               is_new=0""",
            job,
        )
    await db.commit()
    await db.close()


async def get_jobs(
    source: str | None = None,
    category: str | None = None,
    job_type: str | None = None,
    min_score: int = 0,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Fetch jobs with optional filters."""
    db = await get_db()
    query = "SELECT * FROM jobs WHERE score >= ?"
    params: list = [min_score]

    if source:
        query += " AND source = ?"
        params.append(source)
    if category:
        query += " AND category = ?"
        params.append(category)
    if job_type:
        query += " AND job_type = ?"
        params.append(job_type)
    if search:
        query += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    query += " ORDER BY score DESC, scraped_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]


async def get_job_stats():
    """Get summary statistics."""
    db = await get_db()

    cursor = await db.execute("SELECT COUNT(*) as total FROM jobs")
    total = (await cursor.fetchone())["total"]

    cursor = await db.execute(
        "SELECT source, COUNT(*) as count FROM jobs GROUP BY source"
    )
    by_source = {row["source"]: row["count"] for row in await cursor.fetchall()}

    cursor = await db.execute("SELECT AVG(score) as avg_score FROM jobs")
    avg_score = (await cursor.fetchone())["avg_score"] or 0

    cursor = await db.execute(
        "SELECT COUNT(*) as high FROM jobs WHERE score >= 50"
    )
    high_score = (await cursor.fetchone())["high"]

    cursor = await db.execute(
        """SELECT source, scraped_at, status FROM scrape_log
           ORDER BY scraped_at DESC LIMIT 10"""
    )
    recent_scrapes = [dict(row) for row in await cursor.fetchall()]

    await db.close()
    return {
        "total_jobs": total,
        "by_source": by_source,
        "avg_score": round(avg_score, 1),
        "high_score_jobs": high_score,
        "recent_scrapes": recent_scrapes,
    }


async def log_scrape(source: str, job_count: int, status: str = "success", error: str | None = None):
    """Log a scrape run."""
    db = await get_db()
    await db.execute(
        """INSERT INTO scrape_log (source, scraped_at, job_count, status, error_message)
           VALUES (?, ?, ?, ?, ?)""",
        (source, datetime.utcnow().isoformat(), job_count, status, error),
    )
    await db.commit()
    await db.close()
