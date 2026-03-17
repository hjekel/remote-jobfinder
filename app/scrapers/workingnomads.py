"""Working Nomads scraper — uses their public JSON API."""

import hashlib
import logging
from datetime import datetime

import httpx

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job, detect_location_type, detect_contract_type, detect_region

logger = logging.getLogger(__name__)

WORKINGNOMADS_API = "https://www.workingnomads.com/api/exposed_jobs/"


async def scrape_workingnomads() -> int:
    """Fetch jobs from Working Nomads JSON API.

    Returns:
        Number of jobs scraped.
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                WORKINGNOMADS_API,
                headers={"User-Agent": "OpportunityFinder/2.0"},
            )
            resp.raise_for_status()
            data = resp.json()

        jobs = []

        for item in data:
            title = item.get("title", "")
            company = item.get("company_name", "")
            url = item.get("url", "")
            location = item.get("location", "Remote")
            description = item.get("description", "")
            tags = item.get("tags", "")
            category_name = item.get("category_name", "")
            posted = item.get("pub_date", "")

            if not url or not title:
                continue

            job_id = hashlib.md5(f"workingnomads-{url}".encode()).hexdigest()

            full_text = f"{title} {description} {tags} {category_name}"
            score = calculate_score(title, full_text)
            category = categorise_job(title, full_text)
            location_type = detect_location_type(title, full_text, location)
            contract_type = detect_contract_type(title, full_text)
            region = detect_region(title, full_text, location)

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": location[:200] if location else "Remote",
                "url": url,
                "description": description[:2000],
                "source": "WorkingNomads",
                "job_type": "Remote",
                "category": category,
                "location_type": location_type,
                "contract_type": contract_type,
                "region": region,
                "score": score,
                "posted_at": posted,
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
