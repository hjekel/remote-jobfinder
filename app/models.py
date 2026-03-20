"""OpportunityFinder — SQLite database models and helpers."""

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
    location_type TEXT DEFAULT 'remote',
    contract_type TEXT DEFAULT 'unknown',
    region TEXT DEFAULT 'international',
    salary_min INTEGER DEFAULT 0,
    salary_max INTEGER DEFAULT 0,
    tags TEXT DEFAULT '',
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

CREATE TABLE IF NOT EXISTS kanban_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    column_name TEXT NOT NULL DEFAULT 'interested',
    notes TEXT DEFAULT '',
    applied_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
"""

MIGRATIONS = [
    # Add location_type and contract_type if missing (safe to run multiple times)
    "ALTER TABLE jobs ADD COLUMN location_type TEXT DEFAULT 'remote'",
    "ALTER TABLE jobs ADD COLUMN contract_type TEXT DEFAULT 'unknown'",
    "ALTER TABLE jobs ADD COLUMN region TEXT DEFAULT 'international'",
    "ALTER TABLE jobs ADD COLUMN salary_min INTEGER DEFAULT 0",
    "ALTER TABLE jobs ADD COLUMN salary_max INTEGER DEFAULT 0",
    "ALTER TABLE jobs ADD COLUMN tags TEXT DEFAULT ''",
]


async def get_db():
    """Get a database connection."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    """Initialise the database tables and run migrations."""
    db = await get_db()
    await db.executescript(CREATE_TABLES)
    await db.commit()

    # Run migrations (ignore errors for already-existing columns)
    for migration in MIGRATIONS:
        try:
            await db.execute(migration)
            await db.commit()
        except Exception:
            pass

    await db.close()


async def upsert_job(job: dict):
    """Insert or update a job listing."""
    db = await get_db()
    await db.execute(
        """INSERT INTO jobs (id, title, company, location, url, description,
           source, job_type, category, location_type, contract_type, region,
           salary_min, salary_max, tags,
           score, posted_at, scraped_at, is_new)
           VALUES (:id, :title, :company, :location, :url, :description,
           :source, :job_type, :category, :location_type, :contract_type, :region,
           :salary_min, :salary_max, :tags,
           :score, :posted_at, :scraped_at, 1)
           ON CONFLICT(id) DO UPDATE SET
           title=:title, company=:company, location=:location,
           description=:description, score=:score, scraped_at=:scraped_at,
           location_type=:location_type, contract_type=:contract_type,
           category=:category, region=:region,
           salary_min=:salary_min, salary_max=:salary_max, tags=:tags,
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
               source, job_type, category, location_type, contract_type, region,
               salary_min, salary_max, tags,
               score, posted_at, scraped_at, is_new)
               VALUES (:id, :title, :company, :location, :url, :description,
               :source, :job_type, :category, :location_type, :contract_type, :region,
               :salary_min, :salary_max, :tags,
               :score, :posted_at, :scraped_at, 1)
               ON CONFLICT(id) DO UPDATE SET
               title=:title, company=:company, location=:location,
               description=:description, score=:score, scraped_at=:scraped_at,
               location_type=:location_type, contract_type=:contract_type,
               category=:category, region=:region,
               salary_min=:salary_min, salary_max=:salary_max, tags=:tags,
               is_new=0""",
            job,
        )
    await db.commit()
    await db.close()


async def get_jobs(
    source: str | None = None,
    category: str | None = None,
    job_type: str | None = None,
    location_type: str | None = None,
    contract_type: str | None = None,
    region: str | None = None,
    sort_by: str = "score",
    min_score: int = 0,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """Fetch jobs with optional filters.

    Region logic:
    - 'nearby' = remote jobs from anywhere + hybrid/onsite only from
      Noord-Holland, Zuid-Holland, Utrecht, or general Netherlands.
    - Specific region name = only that region.
    - None/empty = no region filtering.
    """
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
    if location_type:
        query += " AND location_type = ?"
        params.append(location_type)
    if contract_type:
        query += " AND contract_type = ?"
        params.append(contract_type)
    if region == "nearby":
        # Remote = anywhere is fine; hybrid/onsite must be in NL target regions
        query += """ AND (
            location_type = 'remote'
            OR region IN ('noord-holland', 'zuid-holland', 'midden-nederland', 'netherlands')
        )"""
    elif region:
        query += " AND region = ?"
        params.append(region)
    if search:
        query += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])

    # Sorting
    sort_options = {
        "score": "score DESC, scraped_at DESC",
        "salary": "salary_max DESC, salary_min DESC, score DESC",
        "date": "posted_at DESC, scraped_at DESC",
    }
    order = sort_options.get(sort_by, sort_options["score"])
    query += f" ORDER BY {order} LIMIT ? OFFSET ?"
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


# --- Kanban board functions ---

async def get_kanban_cards():
    """Fetch all Kanban cards with job details."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT k.*, j.title, j.company, j.url, j.score, j.source,
                  j.category, j.location, j.contract_type,
                  j.salary_min, j.salary_max, j.tags
           FROM kanban_cards k
           JOIN jobs j ON k.job_id = j.id
           ORDER BY k.column_name, k.sort_order"""
    )
    rows = await cursor.fetchall()
    await db.close()
    return [dict(row) for row in rows]


async def add_kanban_card(job_id: str, column: str = "interested"):
    """Add a job to the Kanban board."""
    db = await get_db()
    now = datetime.utcnow().isoformat()

    # Check if already on board
    cursor = await db.execute(
        "SELECT id FROM kanban_cards WHERE job_id = ?", (job_id,)
    )
    existing = await cursor.fetchone()
    if existing:
        await db.close()
        return {"status": "exists", "id": existing["id"]}

    cursor = await db.execute(
        """INSERT INTO kanban_cards (job_id, column_name, created_at, updated_at)
           VALUES (?, ?, ?, ?)""",
        (job_id, column, now, now),
    )
    await db.commit()
    card_id = cursor.lastrowid
    await db.close()
    return {"status": "created", "id": card_id}


async def move_kanban_card(card_id: int, column: str):
    """Move a Kanban card to a different column."""
    db = await get_db()
    now = datetime.utcnow().isoformat()
    applied_at = now if column == "applied" else None

    await db.execute(
        """UPDATE kanban_cards SET column_name = ?, updated_at = ?,
           applied_at = COALESCE(applied_at, ?) WHERE id = ?""",
        (column, now, applied_at, card_id),
    )
    await db.commit()
    await db.close()


async def update_kanban_notes(card_id: int, notes: str):
    """Update notes on a Kanban card."""
    db = await get_db()
    now = datetime.utcnow().isoformat()
    await db.execute(
        "UPDATE kanban_cards SET notes = ?, updated_at = ? WHERE id = ?",
        (notes, now, card_id),
    )
    await db.commit()
    await db.close()


async def delete_kanban_card(card_id: int):
    """Remove a card from the Kanban board."""
    db = await get_db()
    await db.execute("DELETE FROM kanban_cards WHERE id = ?", (card_id,))
    await db.commit()
    await db.close()
