"""OpportunityFinder — AI relevance scoring for job listings.

Scores jobs 0-100 based on keyword matching across tiers.
Broader focus: AI/automation, marketing, lead gen, finance, workshops, consulting.
"""

import re

# Tier 1 - Exact match tools (25 pts each)
TIER_1 = [
    "claude", "claude projects", "claude skills", "claude code", "openclaw",
]

# Tier 2 - AI/LLM general (20 pts each)
TIER_2 = [
    "chatgpt", "gpt-4", "gpt4", "gpt", "gemini", "copilot", "ms copilot",
    "microsoft copilot", "llm", "ai assistant", "ai tools", "ai implementation",
    "ai strategy", "ai transformation", "ai adoption",
]

# Tier 3 - Automation & processing (15 pts each)
TIER_3 = [
    "automation", "workflow automation", "process automation",
    "document processing", "data entry", "document validation", "ocr",
    "repeating tasks", "automate", "task automation", "daily tasks",
    "weekly tasks", "monthly tasks", "periodic tasks", "routine tasks",
    "repetitive tasks", "manual processes",
]

# Tier 3b - Marketing & BizDev (15 pts each)
TIER_3B = [
    "marketing", "business development", "bdr", "sdr", "demand generation",
    "growth", "content marketing", "digital marketing", "marketing automation",
    "email marketing", "crm",
]

# Tier 3c - Lead Gen & Outbound (15 pts each)
TIER_3C = [
    "lead generation", "outbound", "prospecting", "cold outreach",
    "sales development", "pipeline", "lead gen", "outreach automation",
    "linkedin automation",
]

# Tier 3d - Finance & Accounting (15 pts each)
TIER_3D = [
    "finance", "accounting", "bookkeeping", "financial analyst", "controller",
    "accounts payable", "accounts receivable", "audit", "invoicing",
    "financial reporting",
]

# Tier 3e - Workshops & Training (15 pts each)
TIER_3E = [
    "workshop", "training", "ai training", "ai workshop", "ai coaching",
    "digital transformation", "change management", "upskilling",
    "ai literacy", "copilot training", "copilot implementation",
    "ai consultant", "ai consulting",
]

# Tier 4 - Integration & development (10 pts each)
TIER_4 = [
    "api", "integration", "python", "fastapi", "webhook", "etl",
    "data pipeline", "scraping", "internal tools", "dashboard",
    "app development", "no-code", "low-code", "power automate",
    "zapier", "make.com", "n8n", "power platform", "power apps",
]

# Tier 5 - Sectors/departments (8 pts each)
TIER_5 = [
    "financial", "administrative", "warehouse", "logistics",
    "sales", "operations", "hr", "recruitment", "back-office",
    "back office", "supply chain", "procurement", "customer service",
    "healthcare", "legal", "education",
]

# Tier 6 - General relevance (5 pts each)
TIER_6 = [
    "remote", "freelance", "consultant", "b2b", "contractor",
    "project-based", "project based", "fractional", "part-time",
    "interim", "temporary", "contract",
]

TIERS = [
    (TIER_1, 25),
    (TIER_2, 20),
    (TIER_3, 15),
    (TIER_3B, 15),
    (TIER_3C, 15),
    (TIER_3D, 15),
    (TIER_3E, 15),
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

    Returns one of the expanded categories.
    """
    text = f"{title} {description}".lower()

    ai_keywords = {"ai", "machine learning", "ml", "llm", "gpt", "claude",
                   "chatgpt", "copilot", "gemini", "neural", "deep learning",
                   "ai assistant", "ai tools", "ai implementation"}
    auto_keywords = {"automation", "automate", "workflow", "rpa", "process",
                     "ocr", "document processing", "data entry", "power automate",
                     "zapier", "make.com", "n8n", "repetitive", "routine"}
    marketing_keywords = {"marketing", "business development", "bdr", "sdr",
                          "demand generation", "growth", "content marketing",
                          "digital marketing", "brand"}
    leadgen_keywords = {"lead generation", "outbound", "prospecting",
                        "cold outreach", "sales development", "pipeline",
                        "lead gen", "outreach"}
    sales_keywords = {"sales", "sales automation", "crm", "revenue",
                      "account executive", "account manager"}
    finance_keywords = {"finance", "accounting", "bookkeeping", "controller",
                        "audit", "invoicing", "financial", "accounts payable"}
    ops_keywords = {"operations", "admin", "administrative", "back-office",
                    "office manager", "logistics", "warehouse", "supply chain"}
    workshop_keywords = {"workshop", "training", "coaching", "upskilling",
                         "digital transformation", "change management",
                         "ai literacy", "consultant"}
    dev_keywords = {"developer", "development", "engineer", "programming",
                    "python", "javascript", "fastapi", "full stack", "backend"}
    int_keywords = {"integration", "api", "etl", "pipeline", "webhook",
                    "middleware", "connector"}

    if any(kw in text for kw in ai_keywords):
        return "AI & Automation"
    if any(kw in text for kw in auto_keywords):
        return "AI & Automation"
    if any(kw in text for kw in workshop_keywords):
        return "Workshops & Training"
    if any(kw in text for kw in leadgen_keywords):
        return "Lead Gen & Outbound"
    if any(kw in text for kw in marketing_keywords):
        return "Marketing & BizDev"
    if any(kw in text for kw in sales_keywords):
        return "Sales & Sales Automation"
    if any(kw in text for kw in finance_keywords):
        return "Finance & Accounting"
    if any(kw in text for kw in ops_keywords):
        return "Operations & Admin"
    if any(kw in text for kw in int_keywords):
        return "Integration"
    if any(kw in text for kw in dev_keywords):
        return "Development"
    return "General"


def detect_location_type(title: str, description: str = "", location: str = "") -> str:
    """Detect whether a job is remote, hybrid, or on-site.

    Returns: 'remote', 'hybrid', or 'onsite'.
    """
    text = f"{title} {description} {location}".lower()

    if any(kw in text for kw in ["hybrid", "partly remote", "deels remote"]):
        return "hybrid"
    if any(kw in text for kw in ["on-site", "onsite", "on site", "in office",
                                  "in-office", "op locatie", "op kantoor"]):
        return "onsite"
    return "remote"


def detect_region(title: str, description: str = "", location: str = "") -> str:
    """Detect the geographic region from job listing text.

    Returns:
        'noord-holland' — Haarlem, Amsterdam, Zaandam, etc.
        'zuid-holland' — Leiden, Den Haag, Rotterdam, etc.
        'utrecht' — Utrecht city and province
        'netherlands' — Other NL locations
        'international' — Non-NL or unspecified
    """
    text = f"{title} {description} {location}".lower()

    # Noord-Holland cities and areas
    nh_keywords = [
        "haarlem", "amsterdam", "zaandam", "zaanstad", "hoofddorp",
        "schiphol", "amstelveen", "haarlemmermeer", "ijmuiden",
        "velsen", "heemstede", "bloemendaal", "beverwijk",
        "alkmaar", "hilversum", "noord-holland", "north holland",
    ]
    # Zuid-Holland cities and areas
    zh_keywords = [
        "leiden", "den haag", "the hague", "'s-gravenhage", "rotterdam",
        "delft", "zoetermeer", "dordrecht", "gouda", "alphen",
        "katwijk", "leidschendam", "voorburg", "wassenaar",
        "zuid-holland", "south holland",
    ]
    # Utrecht province
    ut_keywords = [
        "utrecht", "amersfoort", "nieuwegein", "veenendaal",
        "zeist", "houten", "woerden", "ijsselstein",
    ]
    # General Netherlands
    nl_keywords = [
        "netherlands", "nederland", "dutch", "holland",
        "eindhoven", "groningen", "breda", "tilburg", "arnhem",
        "nijmegen", "enschede", "maastricht", "den bosch",
        "'s-hertogenbosch", "zwolle", "apeldoorn", "leeuwarden",
    ]

    if any(kw in text for kw in nh_keywords):
        return "noord-holland"
    if any(kw in text for kw in zh_keywords):
        return "zuid-holland"
    if any(kw in text for kw in ut_keywords):
        return "utrecht"
    if any(kw in text for kw in nl_keywords):
        return "netherlands"
    return "international"


def detect_contract_type(title: str, description: str = "") -> str:
    """Detect the contract type from job listing text.

    Returns: 'freelance', 'contract', 'part-time', 'full-time', 'fractional', or 'unknown'.
    """
    text = f"{title} {description}".lower()

    if any(kw in text for kw in ["freelance", "freelancer", "zzp"]):
        return "freelance"
    if any(kw in text for kw in ["fractional", "interim"]):
        return "fractional"
    if any(kw in text for kw in ["part-time", "part time", "parttime", "deeltijd"]):
        return "part-time"
    if any(kw in text for kw in ["contract", "contractor", "temporary", "temp",
                                  "tijdelijk", "opdracht"]):
        return "contract"
    if any(kw in text for kw in ["full-time", "full time", "fulltime", "voltijd",
                                  "permanent"]):
        return "full-time"
    return "unknown"
