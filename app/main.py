"""Remote JobFinder — FastAPI application.

Scrapes remote job boards for AI/automation freelance opportunities.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.models import get_jobs, get_job_stats, init_db
from app.scrapers.remoteok import scrape_remoteok
from app.scrapers.weworkremotely import scrape_weworkremotely
from app.scrapers.remoteco import scrape_remoteco
from app.scrapers.jobspresso import scrape_jobspresso
from app.scrapers.workingnomads import scrape_workingnomads

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALL_SCRAPERS = [
    ("RemoteOK", scrape_remoteok),
    ("WeWorkRemotely", scrape_weworkremotely),
    ("Remote.co", scrape_remoteco),
    ("Jobspresso", scrape_jobspresso),
    ("WorkingNomads", scrape_workingnomads),
]


async def run_all_scrapers():
    """Run all scrapers concurrently."""
    logger.info("Starting scheduled scrape run...")
    tasks = [scraper() for _, scraper in ALL_SCRAPERS]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for (name, _), result in zip(ALL_SCRAPERS, results):
        if isinstance(result, Exception):
            logger.error(f"Scraper {name} failed: {result}")
        else:
            logger.info(f"Scraper {name}: {result} jobs")
    logger.info("Scrape run complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise DB and start scheduler on startup."""
    await init_db()
    logger.info("Database initialised.")

    # Run initial scrape
    asyncio.create_task(run_all_scrapers())

    # Schedule scrapes every 6 hours
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_all_scrapers, "interval", hours=6)
    scheduler.start()
    logger.info("Scheduler started (every 6 hours).")

    yield

    scheduler.shutdown()


app = FastAPI(
    title="Remote JobFinder",
    description="Scrapes remote job boards for AI/automation freelance opportunities.",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/jobs")
async def api_jobs(
    source: str | None = Query(None),
    category: str | None = Query(None),
    job_type: str | None = Query(None),
    min_score: int = Query(0),
    search: str | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    """Fetch job listings with optional filters."""
    jobs = await get_jobs(
        source=source,
        category=category,
        job_type=job_type,
        min_score=min_score,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/stats")
async def api_stats():
    """Get dashboard statistics."""
    return await get_job_stats()


@app.post("/api/scrape")
async def api_scrape():
    """Trigger a manual scrape run."""
    asyncio.create_task(run_all_scrapers())
    return {"status": "Scrape started", "timestamp": datetime.utcnow().isoformat()}
