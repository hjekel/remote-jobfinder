"""RemoteOK scraper — uses their public JSON API."""

import hashlib
import logging
from datetime import datetime

import httpx

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job, detect_location_type, detect_contract_type

logger = logging.getLogger(__name__)

REMOTEOK_URL = "https://remoteok.com/api"


async def scrape_remoteok() -> int:
    """Fetch jobs from RemoteOK JSON API.

    Returns:
        Number of jobs scraped.
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                REMOTEOK_URL,
                headers={"User-Agent": "RemoteJobFinder/1.0"},
            )
            resp.raise_for_status()
            data = resp.json()

        # First item is metadata, skip it
        listings = data[1:] if len(data) > 1 else []
        jobs = []

        for item in listings:
            title = item.get("position", "")
            company = item.get("company", "")
            description = item.get("description", "")
            url = item.get("url", "")
            if url and not url.startswith("http"):
                url = f"https://remoteok.com{url}"
            location = item.get("location", "Remote")
            posted = item.get("date", "")
            tags = ", ".join(item.get("tags", []))

            job_id = hashlib.md5(f"remoteok-{item.get('id', url)}".encode()).hexdigest()

            full_text = f"{title} {description} {tags}"
            score = calculate_score(title, full_text)
            category = categorise_job(title, full_text)
            location_type = detect_location_type(title, full_text, location)
            contract_type = detect_contract_type(title, full_text)

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "url": url,
                "description": description[:2000],
                "source": "RemoteOK",
                "job_type": "Remote",
                "category": category,
                "location_type": location_type,
                "contract_type": contract_type,
                "score": score,
                "posted_at": posted,
                "scraped_at": datetime.utcnow().isoformat(),
            })

        if jobs:
            await upsert_jobs(jobs)

        await log_scrape("RemoteOK", len(jobs))
        logger.info(f"RemoteOK: scraped {len(jobs)} jobs")
        return len(jobs)

    except Exception as e:
        logger.error(f"RemoteOK scraper error: {e}")
        await log_scrape("RemoteOK", 0, status="error", error=str(e))
        return 0
