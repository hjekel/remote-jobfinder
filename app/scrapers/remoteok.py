"""RemoteOK scraper — uses their public JSON API."""

import asyncio
import hashlib
import logging
from datetime import datetime

import httpx

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job, detect_location_type, detect_contract_type, detect_region

logger = logging.getLogger(__name__)

REMOTEOK_URL = "https://remoteok.com/api"

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://remoteok.com/",
}


async def scrape_remoteok() -> int:
    """Fetch jobs from RemoteOK JSON API.

    Uses browser-like headers to avoid 403 blocking on cloud IPs.

    Returns:
        Number of jobs scraped.
    """
    try:
        # Small delay to be polite
        await asyncio.sleep(2)

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(REMOTEOK_URL, headers=BROWSER_HEADERS)
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
            raw_tags = item.get("tags", [])
            tags = ", ".join(raw_tags)
            salary_min = item.get("salary_min", 0) or 0
            salary_max = item.get("salary_max", 0) or 0

            job_id = hashlib.md5(f"remoteok-{item.get('id', url)}".encode()).hexdigest()

            full_text = f"{title} {description} {tags}"
            score = calculate_score(title, full_text)
            category = categorise_job(title, full_text)
            location_type = detect_location_type(title, full_text, location)
            contract_type = detect_contract_type(title, full_text)
            region = detect_region(title, full_text, location)

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
                "region": region,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "tags": tags,
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
