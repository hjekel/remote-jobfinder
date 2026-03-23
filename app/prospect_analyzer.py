"""OpportunityFinder — Prospect text analyser.

Analyses pasted text (website, article, vacancy, LinkedIn post) to detect
AI/automation signals and score the prospect for Henk's services.
"""

import re
from urllib.parse import urlparse


# Signal keyword tiers — same scoring philosophy as job scorer
SIGNAL_TIERS = {
    "ai_direct": {
        "keywords": [
            "ai implementeren", "artificial intelligence", "machine learning",
            "chatgpt", "claude", "copilot", "llm", "ai strategie",
            "ai transformatie", "ai adoptie", "generative ai", "agentic",
            "ai-powered", "ai automation", "ai agent",
        ],
        "score": 25,
        "signal_name": "Direct AI interest",
    },
    "automation": {
        "keywords": [
            "automatiseren", "automation", "workflow", "efficiëntie",
            "processen optimaliseren", "digitalisering", "digital transformation",
            "robotic process", "rpa", "no-code", "low-code",
        ],
        "score": 20,
        "signal_name": "Automation interest",
    },
    "use_cases": {
        "keywords": [
            "document processing", "data entry", "lead generation",
            "sales automation", "marketing automation", "customer service",
            "chatbot", "rapportage", "forecasting", "pipeline",
            "outbound", "prospecting", "onboarding", "coaching",
        ],
        "score": 15,
        "signal_name": "Specific use case",
    },
    "tech_stack": {
        "keywords": [
            "microsoft 365", "dynamics", "salesforce", "hubspot",
            "sap", "oracle", "api", "integratie", "python", "cloud",
            "azure", "aws", "business central", "power platform",
        ],
        "score": 10,
        "signal_name": "Relevant tech stack",
    },
    "profile": {
        "keywords": [
            "b2b", "saas", "scale-up", "groei", "expanding",
            "innovatief", "marktleider", "snelgroeiend", "series a",
            "series b", "funding", "startup",
        ],
        "score": 8,
        "signal_name": "Interesting company profile",
    },
    "hiring": {
        "keywords": [
            "vacature", "hiring", "zoeken", "team uitbreiden",
            "nieuwe collega", "we zoeken", "join us", "open position",
        ],
        "score": 5,
        "signal_name": "Hiring/growth signal",
    },
}

# Relevant case studies to suggest based on detected keywords
CASE_STUDY_MAP = {
    "sales": "Mention BoxIT case study (20 to 500+ leads/month).",
    "lead": "Mention BoxIT case study (25x lead increase).",
    "outbound": "Mention BoxIT outbound pipeline case study.",
    "document": "Mention PlanBit case study (92% time saved on bids).",
    "data entry": "Mention PlanBit case study (92% time saved on bids).",
    "pricing": "Mention PlanBit AI pricing calculator.",
    "dynamics": "Mention Canenco MS Dynamics BC integration.",
    "microsoft": "Mention Canenco MS Dynamics BC integration.",
    "business central": "Mention Canenco MS Dynamics BC integration.",
}


def analyse_prospect(
    source_text: str,
    source_type: str = "other",
    source_url: str = "",
    company_name: str = "",
) -> dict:
    """Analyse pasted text to detect AI/automation fit signals.

    Args:
        source_text: The text to analyse (website copy, article, vacancy, etc.).
        source_type: One of 'website', 'article', 'vacancy', 'linkedin_post', 'other'.
        source_url: Optional URL where the text came from.
        company_name: Optional company name (auto-detected from URL if empty).

    Returns:
        dict with ai_score, ai_summary, ai_signals, suggested_contacts,
        suggested_approach, category, priority, company_name.
    """
    text_lower = source_text.lower()

    # --- Detect signals ---
    signals = []
    for tier_key, tier in SIGNAL_TIERS.items():
        for keyword in tier["keywords"]:
            if keyword.lower() in text_lower:
                # Find context around the keyword
                pattern = rf".{{0,60}}{re.escape(keyword)}.{{0,60}}"
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                quote = matches[0].strip() if matches else keyword

                signals.append({
                    "signal": tier["signal_name"],
                    "keyword": keyword,
                    "quote": quote[:120],
                    "score": tier["score"],
                })
                break  # One match per tier is enough

    # --- Score ---
    score = min(sum(s["score"] for s in signals), 100)

    # --- Company name ---
    if not company_name and source_url:
        try:
            parsed = urlparse(source_url)
            domain = parsed.hostname or ""
            domain = domain.replace("www.", "")
            company_name = domain.split(".")[0].title() if domain else ""
        except Exception:
            pass

    # --- Suggested contacts ---
    contacts = [{"title": "CEO / Founder", "reason": "Direct decision maker for AI investments"}]
    signal_kws = " ".join(s["keyword"] for s in signals).lower()

    if any(kw in signal_kws for kw in ["sales", "lead", "outbound", "pipeline"]):
        contacts.append({"title": "VP Sales / CRO", "reason": "Sales automation focus detected"})
    if any(kw in signal_kws for kw in ["marketing", "content", "campaign"]):
        contacts.append({"title": "CMO / Head of Marketing", "reason": "Marketing automation focus"})
    if any(kw in signal_kws for kw in ["dynamics", "microsoft", "api", "python", "cloud"]):
        contacts.append({"title": "CTO / IT Director", "reason": "Technical implementation"})

    contacts = contacts[:3]

    # --- Suggested approach ---
    approaches = []
    if score >= 60:
        approaches.append("High fit — direct AI implementation pitch.")
    elif score >= 40:
        approaches.append("Medium fit — offer free AI Readiness Scan.")
    else:
        approaches.append("Lower fit — nurture via LinkedIn content first.")

    for kw_trigger, case_study in CASE_STUDY_MAP.items():
        if kw_trigger in signal_kws:
            approaches.append(case_study)
            break

    # --- Category ---
    category = "ai_automation"
    for s in signals:
        kw = s["keyword"].lower()
        if any(x in kw for x in ["sales", "lead", "outbound", "crm", "pipeline"]):
            category = "sales_automation"
            break
        if any(x in kw for x in ["marketing", "content", "campaign"]):
            category = "marketing_automation"
            break
        if any(x in kw for x in ["document", "data entry", "processing"]):
            category = "document_processing"
            break
        if any(x in kw for x in ["dynamics", "business central", "sap"]):
            category = "erp_integration"
            break

    # --- Priority ---
    priority = "high" if score >= 60 else "medium" if score >= 30 else "low"

    # --- Summary ---
    if signals:
        top_signals = sorted(signals, key=lambda x: x["score"], reverse=True)[:3]
        signal_names = [s["signal"] for s in top_signals]
        summary = f"Detected: {', '.join(signal_names)}. Score: {score}/100."
    else:
        summary = "No clear AI/automation signals detected."

    return {
        "company_name": company_name,
        "ai_score": score,
        "ai_summary": summary,
        "ai_signals": signals,
        "suggested_contacts": contacts,
        "suggested_approach": " ".join(approaches),
        "category": category,
        "priority": priority,
    }
