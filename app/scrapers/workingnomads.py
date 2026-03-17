"""Working Nomads scraper — HTML scraping."""

import hashlib
import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job

logger = logging.getLogger(__name__)

WORKINGNOMADS_URL = "https://www.workingnomads.com/jobs"


async def scrape_workingnomads() -> int:
    """Fetch jobs from Working Nomads by scraping HTML.

    Returns:
        Number of jobs scraped.
    """
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(
                WORKINGNOMADS_URL,
                headers={"User-Agent": "RemoteJobFinder/1.0"},
            )
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        jobs = []

        # Working Nomads lists jobs in table rows or divs
        listings = soup.select(".job-item, .job-listing, tr.job, .jobs-list a")
        if not listings:
            # Try broader selectors
            listings = soup.select("a[href*='/jobs/']")

        for listing in listings:
            if listing.name == "a":
                url = listing.get("href", "")
                title = listing.get_text(strip=True)[:100]
                link = listing
            else:
                link = listing.select_one("a[href]")
                if not link:
                    continue
                url = link.get("href", "")
                title_el = listing.select_one("h3, h4, .title, .position")
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)[:100]

            if not url:
                continue
            if not url.startswith("http"):
                url = f"https://www.workingnomads.com{url}"

            company_el = listing.select_one(".company, .employer") if listing.name != "a" else None
            company = company_el.get_text(strip=True) if company_el else ""

            job_id = hashlib.md5(f"workingnomads-{url}".encode()).hexdigest()
            score = calculate_score(title, "")
            category = categorise_job(title, "")

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": "Remote",
                "url": url,
                "description": "",
                "source": "WorkingNomads",
                "job_type": "Remote",
                "category": category,
                "score": score,
                "posted_at": "",
                "scraped_at": datetime.utcnow().isoformat(),
            })

        if jobs:
            await upsert_jobs(jobs)

        await log_scrape("WorkingNomads", len(jobs))
        logger.info(f"WorkingNomads: scraped {len(jobs)} jobs")
        return len(jobs)

    except Exception as e:
        logger.error(f"WorkingNomads scraper error: {e}")
        await log_scrape("WorkingNomads", 0, status="error", error=str(e))
        return 0
