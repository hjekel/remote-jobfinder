"""Remote.co scraper — HTML scraping."""

import hashlib
import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job

logger = logging.getLogger(__name__)

REMOTECO_URL = "https://remote.co/remote-jobs/"


async def scrape_remoteco() -> int:
    """Fetch jobs from Remote.co by scraping HTML.

    Returns:
        Number of jobs scraped.
    """
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(
                REMOTECO_URL,
                headers={"User-Agent": "RemoteJobFinder/1.0"},
            )
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        jobs = []

        # Remote.co lists jobs in anchor tags with class 'card'
        job_cards = soup.select("a.card")
        if not job_cards:
            # Fallback: try other common selectors
            job_cards = soup.select(".job_listing a, .job-listing a, article a")

        for card in job_cards:
            url = card.get("href", "")
            if not url or "/remote-jobs/" not in url:
                continue
            if not url.startswith("http"):
                url = f"https://remote.co{url}"

            title_el = card.select_one("h3, .position, .job-title, strong")
            title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)[:100]

            company_el = card.select_one(".company, .employer, p")
            company = company_el.get_text(strip=True) if company_el else ""

            job_id = hashlib.md5(f"remoteco-{url}".encode()).hexdigest()
            score = calculate_score(title, "")
            category = categorise_job(title, "")

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": "Remote",
                "url": url,
                "description": "",
                "source": "Remote.co",
                "job_type": "Remote",
                "category": category,
                "score": score,
                "posted_at": "",
                "scraped_at": datetime.utcnow().isoformat(),
            })

        if jobs:
            await upsert_jobs(jobs)

        await log_scrape("Remote.co", len(jobs))
        logger.info(f"Remote.co: scraped {len(jobs)} jobs")
        return len(jobs)

    except Exception as e:
        logger.error(f"Remote.co scraper error: {e}")
        await log_scrape("Remote.co", 0, status="error", error=str(e))
        return 0
