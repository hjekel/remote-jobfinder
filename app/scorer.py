"""OpportunityFinder — AI relevance scoring for job listings.

Scores jobs 0-100 based on keyword matching across tiers.
Broader focus: AI/automation, marketing, lead gen, finance, workshops, consulting.
"""

import re

# Tier 1 - Exact match tools (25 pts each)
TIER_1 = [
    "claude", "claude projects", "claude skills", "claude code", "openclaw",
    "cursor", "windsurf", "lovable", "replit agent", "v0.dev",
]

# Tier 2 - AI/LLM & AI-building (20 pts each)
TIER_2 = [
    "chatgpt", "gpt-4", "gpt4", "gpt", "gemini", "copilot", "ms copilot",
    "microsoft copilot", "llm", "ai assistant", "ai tools", "ai implementation",
    "ai strategy", "ai transformation", "ai adoption",
    "prompt engineering", "ai-native", "ai native", "ai builder",
    "build with ai", "ai-powered", "ai powered",
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
    "email marketing", "crm", "personalised marketing", "personalized marketing",
    "abm", "account-based marketing", "account based marketing",
    "marketing strategy", "brand strategy", "growth marketing",
    "performance marketing", "inbound marketing",
]

# Tier 3c - Lead Gen & Outbound (15 pts each)
TIER_3C = [
    "lead generation", "outbound", "prospecting", "cold outreach",
    "sales development", "pipeline", "lead gen", "outreach automation",
    "linkedin automation", "outbound lead generation",
    "demand gen", "revenue operations", "revops",
    "sales enablement", "sales ops",
]

# Tier 3d - Finance & Accounting (15 pts each)
TIER_3D = [
    "finance", "accounting", "bookkeeping", "financial analyst", "controller",
    "accounts payable", "accounts receivable", "audit", "invoicing",
    "financial reporting", "fintech", "payments",
]

# Tier 3e - Workshops, Coaching & Training (15 pts each)
TIER_3E = [
    "workshop", "training", "ai training", "ai workshop", "ai coaching",
    "digital transformation", "change management", "upskilling",
    "ai literacy", "copilot training", "copilot implementation",
    "ai consultant", "ai consulting",
    "coaching", "mentoring", "onboarding", "enablement",
    "bdr onboarding", "sdr onboarding", "sales onboarding",
    "team coaching", "sales coaching", "inside sales",
]

# Tier 3f - Strategy & GTM (15 pts each)
TIER_3F = [
    "gtm", "go-to-market", "go to market", "market expansion",
    "geo expansion", "expansion strategy", "product roadmap",
    "market positioning", "market entry", "business case",
    "strategy leader", "strategy manager", "strategic partnerships",
    "product-market fit", "product market fit", "pmf",
]

# Tier 4 - Integration & development (10 pts each)
TIER_4 = [
    "api", "integration", "python", "fastapi", "webhook", "etl",
    "data pipeline", "scraping", "internal tools", "dashboard",
    "app development", "no-code", "low-code", "power automate",
    "zapier", "make.com", "n8n", "power platform", "power apps",
    "airtable", "notion", "hubspot",
]

# Tier 5 - Sectors/departments (8 pts each)
TIER_5 = [
    "financial", "administrative", "warehouse", "logistics",
    "sales", "operations", "hr", "recruitment", "back-office",
    "back office", "supply chain", "procurement", "customer service",
    "healthcare", "legal", "education", "saas", "b2b saas",
    "smb", "startup", "scaleup", "scale-up",
]

# Tier 6 - General relevance (5 pts each)
TIER_6 = [
    "remote", "freelance", "consultant", "b2b", "contractor",
    "project-based", "project based", "fractional", "part-time",
    "interim", "temporary", "contract", "emea", "europe",
]

TIERS = [
    (TIER_1, 25),
    (TIER_2, 20),
    (TIER_3, 15),
    (TIER_3B, 15),
    (TIER_3C, 15),
    (TIER_3D, 15),
    (TIER_3E, 15),
    (TIER_3F, 15),
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
                   "ai assistant", "ai tools", "ai implementation",
                   "prompt engineering", "ai-native", "ai builder",
                   "cursor", "windsurf", "lovable", "claude code"}
    auto_keywords = {"automation", "automate", "workflow", "rpa", "process",
                     "ocr", "document processing", "data entry", "power automate",
                     "zapier", "make.com", "n8n", "repetitive", "routine"}
    marketing_keywords = {"marketing", "business development", "bdr", "sdr",
                          "demand generation", "growth", "content marketing",
                          "digital marketing", "brand", "abm",
                          "account-based marketing", "performance marketing",
                          "inbound marketing", "personalised marketing",
                          "personalized marketing", "growth marketing"}
    leadgen_keywords = {"lead generation", "outbound", "prospecting",
                        "cold outreach", "sales development", "pipeline",
                        "lead gen", "outreach", "demand gen", "revops",
                        "revenue operations", "outbound lead generation"}
    gtm_keywords = {"gtm", "go-to-market", "go to market", "market expansion",
                    "geo expansion", "expansion strategy", "product roadmap",
                    "market entry", "strategic partnerships", "product-market fit"}
    coaching_keywords = {"coaching", "mentoring", "onboarding", "enablement",
                         "bdr onboarding", "sdr onboarding", "sales onboarding",
                         "team coaching", "sales coaching", "inside sales"}
    sales_keywords = {"sales", "sales automation", "crm", "revenue",
                      "account executive", "account manager"}
    finance_keywords = {"finance", "accounting", "bookkeeping", "controller",
                        "audit", "invoicing", "financial", "accounts payable",
                        "fintech", "payments"}
    ops_keywords = {"operations", "admin", "administrative", "back-office",
                    "office manager", "logistics", "warehouse", "supply chain"}
    workshop_keywords = {"workshop", "training", "ai training", "upskilling",
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
    if any(kw in text for kw in gtm_keywords):
        return "Strategy & GTM"
    if any(kw in text for kw in coaching_keywords):
        return "Coaching & Enablement"
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
        'midden-nederland' — Utrecht, Gelderland, Flevoland
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
        "purmerend", "hoorn", "den helder", "heerhugowaard",
    ]
    # Zuid-Holland cities and areas
    zh_keywords = [
        "leiden", "den haag", "the hague", "'s-gravenhage", "rotterdam",
        "delft", "zoetermeer", "dordrecht", "gouda", "alphen",
        "katwijk", "leidschendam", "voorburg", "wassenaar",
        "zuid-holland", "south holland",
        "schiedam", "vlaardingen", "rijswijk", "capelle",
    ]
    # Midden-Nederland — Utrecht + Gelderland + Flevoland
    mn_keywords = [
        "utrecht", "amersfoort", "nieuwegein", "veenendaal",
        "zeist", "houten", "woerden", "ijsselstein",
        "arnhem", "nijmegen", "apeldoorn", "ede", "wageningen",
        "barneveld", "harderwijk", "doetinchem", "tiel",
        "gelderland", "flevoland", "almere", "lelystad",
        "midden-nederland", "midden nederland",
    ]
    # General Netherlands
    nl_keywords = [
        "netherlands", "nederland", "dutch", "holland",
        "eindhoven", "groningen", "breda", "tilburg",
        "enschede", "maastricht", "den bosch",
        "'s-hertogenbosch", "zwolle", "leeuwarden",
        "heerlen", "venlo", "deventer", "emmen",
        "noord-brabant", "limburg", "overijssel", "drenthe",
        "friesland", "zeeland",
    ]

    if any(kw in text for kw in nh_keywords):
        return "noord-holland"
    if any(kw in text for kw in zh_keywords):
        return "zuid-holland"
    if any(kw in text for kw in mn_keywords):
        return "midden-nederland"
    if any(kw in text for kw in nl_keywords):
        return "netherlands"
    return "international"


def detect_contract_type(title: str, description: str = "") -> str:
    """Detect the contract type from job listing text.

    Returns: 'freelance', 'fractional', 'project', 'temporary', 'part-time',
             'contract', 'full-time', or 'unknown'.
    """
    text = f"{title} {description}".lower()

    if any(kw in text for kw in ["freelance", "freelancer", "zzp"]):
        return "freelance"
    if any(kw in text for kw in ["fractional", "interim"]):
        return "fractional"
    if any(kw in text for kw in ["project-based", "project based", "projectbasis",
                                  "short-term project", "kortlopend project",
                                  "opdracht"]):
        return "project"
    if any(kw in text for kw in ["temporary", "temp ", "tijdelijk", "fixed-term",
                                  "fixed term", "bepaalde tijd", "kortlopend"]):
        return "temporary"
    if any(kw in text for kw in ["part-time", "part time", "parttime", "deeltijd"]):
        return "part-time"
    if any(kw in text for kw in ["contract", "contractor"]):
        return "contract"
    if any(kw in text for kw in ["full-time", "full time", "fulltime", "voltijd",
                                  "permanent"]):
        return "full-time"
    return "unknown"
