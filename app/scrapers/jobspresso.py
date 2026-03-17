"""Jobspresso scraper — uses WP Job Manager AJAX endpoint."""

import hashlib
import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup

from app.models import upsert_jobs, log_scrape
from app.scorer import calculate_score, categorise_job, detect_location_type, detect_contract_type, detect_region

logger = logging.getLogger(__name__)

JOBSPRESSO_AJAX = "https://jobspresso.co/jm-ajax/get_listings/"


async def scrape_jobspresso() -> int:
    """Fetch jobs from Jobspresso via WP Job Manager AJAX.

    Returns:
        Number of jobs scraped.
    """
    try:
        all_jobs = []
        page = 1
        max_pages = 5  # Limit to first 5 pages to be polite

        async with httpx.AsyncClient(timeout=30) as client:
            while page <= max_pages:
                resp = await client.post(
                    JOBSPRESSO_AJAX,
                    data={
                        "per_page": 25,
                        "page": page,
                        "show_pagination": "false",
                    },
                    headers={
                        "User-Agent": "OpportunityFinder/2.0",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                html_content = data.get("html", "")
                if not html_content or not html_content.strip():
                    break

                soup = BeautifulSoup(html_content, "lxml")
                listings = soup.select("li.job_listing")

                if not listings:
                    break

                for listing in listings:
                    # Extract URL
                    link = listing.select_one("a.job_listing-clickbox")
                    url = ""
                    if link:
                        url = link.get("href", "")
                    elif listing.get("data-href"):
                        url = listing["data-href"]

                    if not url:
                        continue

                    # Extract title
                    title_el = listing.select_one("h3.job_listing-title")
                    title = title_el.get_text(strip=True) if title_el else ""

                    if not title:
                        continue

                    # Extract company
                    company_el = listing.select_one(".job_listing-company strong")
                    company = company_el.get_text(strip=True) if company_el else ""

                    # Extract location
                    loc_el = listing.select_one(".job_listing-location .google_map_link")
                    if not loc_el:
                        loc_el = listing.select_one(".job_listing-location")
                    location = loc_el.get_text(strip=True) if loc_el else "Remote"

                    # Extract job type
                    type_el = listing.select_one("li.job_listing-type, .job-type")
                    job_type_text = type_el.get_text(strip=True) if type_el else ""

                    job_id = hashlib.md5(f"jobspresso-{url}".encode()).hexdigest()
                    score = calculate_score(title, job_type_text)
                    category = categorise_job(title, job_type_text)
                    location_type = detect_location_type(title, "", location)
                    contract_type = detect_contract_type(title, job_type_text)
                    region = detect_region(title, "", location)

                    all_jobs.append({
                        "id": job_id,
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": url,
                        "description": "",
                        "source": "Jobspresso",
                        "job_type": job_type_text or "Remote",
                        "category": category,
                        "location_type": location_type,
                        "contract_type": contract_type,
                        "region": region,
                        "score": score,
                        "posted_at": "",
                        "scraped_at": datetime.utcnow().isoformat(),
                    })

                # Check if there are more pages
                if not data.get("found_jobs", True):
                    break

                page += 1

        if all_jobs:
            await upsert_jobs(all_jobs)

        await log_scrape("Jobspresso", len(all_jobs))
        logger.info(f"Jobspresso: scraped {len(all_jobs)} jobs")
        return len(all_jobs)

    except Exception as e:
        logger.error(f"Jobspresso scraper error: {e}")
        await log_scrape("Jobspresso", 0, status="error", error=str(e))
        return 0
