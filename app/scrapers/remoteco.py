"""Himalayas.app scraper — replaces Remote.co (which blocks all non-browser requests).

Uses the Himalayas public JSON API for remote job listings.
"""

import hashlib
import logging
from datetime import datetime

import httpx

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job, detect_location_type, detect_contract_type, detect_region

logger = logging.getLogger(__name__)

HIMALAYAS_API = "https://himalayas.app/jobs/api"


async def scrape_remoteco() -> int:
    """Fetch jobs from Himalayas.app JSON API.

    Note: Function name kept as scrape_remoteco for backward compatibility
    in main.py, but now sources from Himalayas.app.

    Returns:
        Number of jobs scraped.
    """
    try:
        all_jobs = []
        offset = 0
        limit = 50
        max_pages = 4  # 200 jobs max to be polite

        async with httpx.AsyncClient(timeout=30) as client:
            for _ in range(max_pages):
                resp = await client.get(
                    HIMALAYAS_API,
                    params={"limit": limit, "offset": offset},
                    headers={"User-Agent": "OpportunityFinder/2.0"},
                )
                resp.raise_for_status()
                data = resp.json()

                jobs_data = data.get("jobs", [])
                if not jobs_data:
                    break

                for item in jobs_data:
                    title = item.get("title", "")
                    company = item.get("companyName", "")
                    description = item.get("description", "") or ""
                    categories = ", ".join(item.get("categories", []))
                    seniority = item.get("seniority", "")

                    # Build URL from slug
                    slug = item.get("slug", "")
                    company_slug = item.get("companySlug", "")
                    if slug and company_slug:
                        url = f"https://himalayas.app/companies/{company_slug}/jobs/{slug}"
                    elif item.get("applicationLink"):
                        url = item["applicationLink"]
                    else:
                        url = f"https://himalayas.app/jobs/{slug}" if slug else ""

                    if not url or not title:
                        continue

                    location = ", ".join(item.get("locationRestrictions", [])) or "Remote"
                    posted = item.get("pubDate", "") or item.get("updatedAt", "")
                    salary_min = item.get("minSalary", 0) or 0
                    salary_max = item.get("maxSalary", 0) or 0
                    raw_tags = item.get("categories", [])
                    tags_str = ", ".join(raw_tags)

                    job_id = hashlib.md5(f"himalayas-{slug or url}".encode()).hexdigest()

                    full_text = f"{title} {description[:1000]} {categories} {seniority}"
                    score = calculate_score(title, full_text)
                    category = categorise_job(title, full_text)
                    location_type = detect_location_type(title, full_text, location)
                    contract_type = detect_contract_type(title, full_text)
                    region = detect_region(title, full_text, location)

                    all_jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "location": location[:200],
                        "url": url,
                        "description": description[:2000],
                        "source": "Himalayas",
                        "job_type": "Remote",
                        "category": category,
                        "location_type": location_type,
                        "contract_type": contract_type,
                        "region": region,
                        "salary_min": salary_min,
                        "salary_max": salary_max,
                        "tags": tags_str,
                        "score": score,
                        "posted_at": posted,
                        "scraped_at": datetime.utcnow().isoformat(),
                    })

                offset += limit
                total = data.get("totalCount", 0)
                if offset >= total:
                    break

        if all_jobs:
            await upsert_jobs(all_jobs)

        await log_scrape("Himalayas", len(all_jobs))
        logger.info(f"Himalayas: scraped {len(all_jobs)} jobs")
        return len(all_jobs)

    except Exception as e:
        logger.error(f"Himalayas scraper error: {e}")
        await log_scrape("Himalayas", 0, status="error", error=str(e))
        return 0
