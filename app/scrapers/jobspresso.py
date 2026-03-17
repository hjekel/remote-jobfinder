"""Jobspresso scraper — HTML scraping."""

import hashlib
import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job

logger = logging.getLogger(__name__)

JOBSPRESSO_URL = "https://jobspresso.co/remote-work/"


async def scrape_jobspresso() -> int:
    """Fetch jobs from Jobspresso by scraping HTML.

    Returns:
        Number of jobs scraped.
    """
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(
                JOBSPRESSO_URL,
                headers={"User-Agent": "RemoteJobFinder/1.0"},
            )
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        jobs = []

        # Jobspresso uses job listing containers
        listings = soup.select(".job_listing, .job-listing, article.post")
        if not listings:
            listings = soup.select("li.job_listing")

        for listing in listings:
            link = listing.select_one("a[href]")
            if not link:
                continue

            url = link.get("href", "")
            if not url.startswith("http"):
                url = f"https://jobspresso.co{url}"

            title_el = listing.select_one("h3, h4, .job-title, .position")
            title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)[:100]

            company_el = listing.select_one(".company, .employer, .job-company")
            company = company_el.get_text(strip=True) if company_el else ""

            location_el = listing.select_one(".location, .job-location")
            location = location_el.get_text(strip=True) if location_el else "Remote"

            job_type_el = listing.select_one(".job-type, .type")
            job_type = job_type_el.get_text(strip=True) if job_type_el else "Remote"

            job_id = hashlib.md5(f"jobspresso-{url}".encode()).hexdigest()
            score = calculate_score(title, "")
            category = categorise_job(title, "")

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "description": "",
                "source": "Jobspresso",
                "job_type": job_type,
                "category": category,
                "score": score,
                "posted_at": "",
                "scraped_at": datetime.utcnow().isoformat(),
            })

        if jobs:
            await upsert_jobs(jobs)

        await log_scrape("Jobspresso", len(jobs))
        logger.info(f"Jobspresso: scraped {len(jobs)} jobs")
        return len(jobs)

    except Exception as e:
        logger.error(f"Jobspresso scraper error: {e}")
        await log_scrape("Jobspresso", 0, status="error", error=str(e))
        return 0
