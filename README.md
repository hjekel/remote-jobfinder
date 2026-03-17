# Remote JobFinder

Automatically scrapes remote job boards for AI/automation freelance projects.

## Tech Stack
- **Backend:** FastAPI + Python
- **Frontend:** Vanilla HTML/CSS/JS
- **Database:** SQLite
- **Hosting:** Render.com (free tier)

## Job Sources (Tier 1)
- We Work Remotely (RSS)
- RemoteOK (JSON API)
- Remote.co (HTML scraping)
- Jobspresso (HTML scraping)
- Working Nomads (HTML scraping)

## Running Locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Deployment
Deploys automatically to Render.com on push to main.
