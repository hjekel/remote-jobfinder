"""AI relevance scoring for job listings.

Scores jobs 0-100 based on keyword matching across tiers.
Higher score = more relevant for Henk's AI/automation freelance skills.
"""

import re

# Tier 1 - Exact match tools (25 pts each)
TIER_1 = [
    "claude", "claude projects", "claude skills", "claude code", "openclaw",
]

# Tier 2 - AI/LLM general (20 pts each)
TIER_2 = [
    "chatgpt", "gpt-4", "gpt4", "gpt", "gemini", "copilot", "ms copilot",
    "microsoft copilot", "llm", "ai assistant",
]

# Tier 3 - Automation & processing (15 pts each)
TIER_3 = [
    "automation", "workflow automation", "process automation",
    "document processing", "data entry", "document validation", "ocr",
    "repeating tasks", "automate",
]

# Tier 4 - Integration & development (10 pts each)
TIER_4 = [
    "api", "integration", "python", "fastapi", "webhook", "etl",
    "data pipeline", "scraping", "internal tools", "dashboard",
    "app development",
]

# Tier 5 - Sectors/departments (8 pts each)
TIER_5 = [
    "financial", "finance", "administrative", "warehouse", "logistics",
    "sales", "marketing", "operations", "hr", "recruitment", "back-office",
    "back office",
]

# Tier 6 - General relevance (5 pts each)
TIER_6 = [
    "remote", "freelance", "consultant", "b2b", "contractor",
    "project-based", "project based",
]

TIERS = [
    (TIER_1, 25),
    (TIER_2, 20),
    (TIER_3, 15),
    (TIER_4, 10),
    (TIER_5, 8),
    (TIER_6, 5),
]


def calculate_score(title: str, description: str = "") -> int:
    """Calculate relevance score for a job listing.

    Args:
        title: Job title.
        description: Job description text.

    Returns:
        Score between 0 and 100.
    """
    text = f"{title} {description}".lower()
    score = 0

    for keywords, points in TIERS:
        for keyword in keywords:
            # Use word boundary matching for short keywords to avoid false positives
            if len(keyword) <= 3:
                pattern = rf"\b{re.escape(keyword)}\b"
                if re.search(pattern, text):
                    score += points
            else:
                if keyword in text:
                    score += points

    return min(score, 100)


def categorise_job(title: str, description: str = "") -> str:
    """Categorise a job based on its content.

    Returns one of: AI/ML, Automation, Development, Integration, General.
    """
    text = f"{title} {description}".lower()

    ai_keywords = {"ai", "machine learning", "ml", "llm", "gpt", "claude",
                   "chatgpt", "copilot", "gemini", "neural", "deep learning"}
    auto_keywords = {"automation", "automate", "workflow", "rpa", "process",
                     "ocr", "document processing", "data entry"}
    dev_keywords = {"developer", "development", "engineer", "programming",
                    "python", "javascript", "fastapi", "full stack", "backend"}
    int_keywords = {"integration", "api", "etl", "pipeline", "webhook",
                    "middleware", "connector"}

    if any(kw in text for kw in ai_keywords):
        return "AI/ML"
    if any(kw in text for kw in auto_keywords):
        return "Automation"
    if any(kw in text for kw in int_keywords):
        return "Integration"
    if any(kw in text for kw in dev_keywords):
        return "Development"
    return "General"
