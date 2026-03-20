"""We Work Remotely scraper — uses RSS feeds."""

import hashlib
import logging
from datetime import datetime

import feedparser
import httpx

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job, detect_location_type, detect_contract_type, detect_region

logger = logging.getLogger(__name__)

# RSS feeds for different categories
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/categories/remote-customer-support-jobs.rss",
    "https://weworkremotely.com/categories/remote-product-jobs.rss",
    "https://weworkremotely.com/remote-jobs.rss",
]


async def scrape_weworkremotely() -> int:
    """Fetch jobs from We Work Remotely RSS feeds.

    Returns:
        Number of jobs scraped.
    """
    try:
        all_jobs = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=30) as client:
            for feed_url in WWR_FEEDS:
                try:
                    resp = await client.get(
                        feed_url,
                        headers={"User-Agent": "RemoteJobFinder/1.0"},
                    )
                    resp.raise_for_status()
                    feed = feedparser.parse(resp.text)

                    for entry in feed.entries:
                        url = entry.get("link", "")
                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        title = entry.get("title", "")
                        # WWR titles often have format "Company: Title"
                        company = ""
                        if ": " in title:
                            company, title = title.split(": ", 1)

                        description = entry.get("summary", "")
                        posted = entry.get("published", "")

                        job_id = hashlib.md5(f"wwr-{url}".encode()).hexdigest()
                        score = calculate_score(title, description)
                        category = categorise_job(title, description)
                        location_type = detect_location_type(title, description)
                        contract_type = detect_contract_type(title, description)
                        region = detect_region(title, description)

                        all_jobs.append({
                            "id": job_id,
                            "title": title,
                            "company": company,
                            "location": "Remote",
                            "url": url,
                            "description": description[:2000],
                            "source": "WeWorkRemotely",
                            "job_type": "Remote",
                            "category": category,
                            "location_type": location_type,
                            "contract_type": contract_type,
                            "region": region,
                            "salary_min": 0,
                            "salary_max": 0,
                            "tags": "",
                            "score": score,
                            "posted_at": posted,
                            "scraped_at": datetime.utcnow().isoformat(),
                        })
                except Exception as e:
                    logger.warning(f"WWR feed {feed_url} failed: {e}")
                    continue

        if all_jobs:
            await upsert_jobs(all_jobs)

        await log_scrape("WeWorkRemotely", len(all_jobs))
        logger.info(f"WeWorkRemotely: scraped {len(all_jobs)} jobs")
        return len(all_jobs)

    except Exception as e:
        logger.error(f"WeWorkRemotely scraper error: {e}")
        await log_scrape("WeWorkRemotely", 0, status="error", error=str(e))
        return 0
