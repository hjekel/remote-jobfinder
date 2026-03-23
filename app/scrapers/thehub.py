"""TheHub.io scraper — European tech jobs via their JSON API.

Focuses on EU-based scale-ups and startups with AI, automation,
business development and fractional/interim roles.
"""

import asyncio
import hashlib
import logging
from datetime import datetime

import httpx

from app.models import upsert_jobs, log_scrape
from app.scorer import (
    calculate_score, categorise_job,
    detect_location_type, detect_contract_type, detect_region,
)

logger = logging.getLogger(__name__)

THEHUB_API = "https://thehub.io/api/jobs"

# Search queries covering Henk's target areas
SEARCH_QUERIES = [
    "ai automation",
    "business development",
    "sales marketing SaaS",
    "fractional interim",
    "lead generation outbound",
    "consultant AI",
]

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://thehub.io/jobs",
}


async def scrape_thehub() -> int:
    """Fetch jobs from TheHub.io JSON API.

    Runs multiple search queries to cover AI, BD, marketing and fractional roles.

    Returns:
        Number of unique jobs scraped.
    """
    try:
        seen_ids = set()
        all_jobs = []

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            for query in SEARCH_QUERIES:
                try:
                    # Fetch first 2 pages per query
                    for page in range(1, 3):
                        resp = await client.get(
                            THEHUB_API,
                            params={"q": query, "page": page},
                            headers=BROWSER_HEADERS,
                        )
                        resp.raise_for_status()
                        data = resp.json()

                        docs = data.get("docs", [])
                        if not docs:
                            break

                        for item in docs:
                            job_key = item.get("key", "") or item.get("id", "")
                            if not job_key or job_key in seen_ids:
                                continue
                            seen_ids.add(job_key)

                            parsed = _parse_job(item)
                            if parsed:
                                all_jobs.append(parsed)

                        # Rate limiting — be polite
                        await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(f"TheHub query '{query}' failed: {e}")
                    continue

        if all_jobs:
            await upsert_jobs(all_jobs)

        await log_scrape("TheHub", len(all_jobs))
        logger.info(f"TheHub: scraped {len(all_jobs)} jobs")
        return len(all_jobs)

    except Exception as e:
        logger.error(f"TheHub scraper error: {e}")
        await log_scrape("TheHub", 0, status="error", error=str(e))
        return 0


def _parse_job(item: dict) -> dict | None:
    """Parse a single job from TheHub API response."""
    title = item.get("title", "")
    if not title:
        return None

    # URL
    url = item.get("absoluteJobUrl", "")
    if not url:
        key = item.get("key", "")
        url = f"https://thehub.io/jobs/{key}" if key else ""
    if not url:
        return None

    # Company info
    company_obj = item.get("company", {}) or {}
    company = company_obj.get("name", "")

    # Location — can be a dict or string
    loc_raw = item.get("location", "")
    if isinstance(loc_raw, dict):
        location = loc_raw.get("address", "") or loc_raw.get("locality", "") or loc_raw.get("country", "")
    else:
        location = str(loc_raw) if loc_raw else ""
    country = item.get("countryCode", "")
    is_remote = item.get("isRemote", False)
    if is_remote and not location:
        location = "Remote"
    elif country and not location:
        location = country

    # Description
    description = item.get("description", "") or ""

    # Job type — position types may be IDs, not strings
    position_types = item.get("jobPositionTypes", []) or []
    # Filter out MongoDB-style IDs, keep human-readable strings
    readable_types = [pt for pt in position_types if isinstance(pt, str) and len(pt) < 30 and not pt.startswith("5")]
    job_type_str = ", ".join(readable_types) if readable_types else "Full-time"

    # Salary
    salary_range = item.get("salaryRange", {}) or {}
    salary_min = salary_range.get("min", 0) or 0
    salary_max = salary_range.get("max", 0) or 0

    # Tags from job role and company industries
    tags_parts = []
    job_role = item.get("jobRole", "")
    if job_role:
        tags_parts.append(job_role)
    # Company industries
    industries = company_obj.get("industries", []) or []
    for ind in industries[:3]:
        if isinstance(ind, str):
            tags_parts.append(ind)
        elif isinstance(ind, dict):
            tags_parts.append(ind.get("name", ""))
    tags = ", ".join(t for t in tags_parts if t)

    # Posted date
    posted = item.get("publishedAt", "") or item.get("createdAt", "")

    # Build ID
    job_id = hashlib.md5(f"thehub-{item.get('key', url)}".encode()).hexdigest()

    # Scoring
    full_text = f"{title} {description[:1000]} {tags} {job_type_str}"
    score = calculate_score(title, full_text)
    category = categorise_job(title, full_text)
    location_type = "remote" if is_remote else detect_location_type(title, full_text, location)
    contract_type = detect_contract_type(title, full_text)
    region = detect_region(title, full_text, location)

    return {
        "id": job_id,
        "title": title,
        "company": company,
        "location": location[:200] if location else "Remote",
        "url": url,
        "description": description[:2000],
        "source": "TheHub",
        "job_type": job_type_str,
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
    }
