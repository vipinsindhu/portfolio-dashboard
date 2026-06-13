"""
Canonical sector taxonomy shared across signals, portfolio analysis, and stock discovery.

All sector strings flowing through the app should pass through normalize_sector()
so every tab and every API endpoint uses the same labels.
"""

# These 15 buckets match the TARGET_ALLOCATION keys in analysis.py.
# Every sector string in the system should resolve to one of these.
CANONICAL_SECTORS = {
    "Broad Market Index",
    "International Equities",
    "Technology",
    "Financials",
    "Healthcare",
    "Consumer",
    "Industrials",
    "Energy",
    "Utilities",
    "Materials",
    "Real Estate",
    "Bonds",
    "Commodities",
    "Cryptocurrencies",
    "Other",
}

# Maps any lowercase non-canonical name → canonical bucket.
# Covers Finnhub finnhubIndustry strings, GICS names, and legacy internal names.
_ALIASES: dict[str, str] = {
    # Consumer (Discretionary + Staples + Retail + Food)
    "consumer discretionary": "Consumer",
    "consumer staples": "Consumer",
    "retail & e-commerce": "Consumer",
    "retail": "Consumer",
    "food & beverage": "Consumer",
    "beverages": "Consumer",
    "food products": "Consumer",
    "diversified consumer services": "Consumer",
    "consumer services": "Consumer",
    "restaurants": "Consumer",
    "hotels, restaurants & leisure": "Consumer",
    "textiles, apparel & luxury goods": "Consumer",
    "household products": "Consumer",
    "personal products": "Consumer",
    # Technology (including Semiconductors, Software, Comms-adjacent)
    "semiconductors": "Technology",
    "software": "Technology",
    "internet": "Technology",
    "it services": "Technology",
    "communications": "Technology",
    "communication services": "Technology",
    "electronic equipment": "Technology",
    "computers & peripherals": "Technology",
    # Healthcare (Pharma + Biotech + Life Sciences + Medtech)
    "pharma & biotech": "Healthcare",
    "biotechnology": "Healthcare",
    "pharmaceuticals": "Healthcare",
    "life sciences tools & services": "Healthcare",
    "medical devices": "Healthcare",
    "medical": "Healthcare",
    "health care equipment & supplies": "Healthcare",
    "health care providers & services": "Healthcare",
    "managed health care": "Healthcare",
    # Financials (Banks + Insurance + Investment)
    "banking": "Financials",
    "banks": "Financials",
    "insurance": "Financials",
    "financial services": "Financials",
    "diversified financials": "Financials",
    "capital markets": "Financials",
    "investment banking & brokerage": "Financials",
    "asset management": "Financials",
    # Industrials (Defense + Airlines + Building + Transport)
    "defense & aerospace": "Industrials",
    "aerospace & defense": "Industrials",
    "airlines": "Industrials",
    "air freight & logistics": "Industrials",
    "building": "Industrials",
    "building products": "Industrials",
    "construction": "Industrials",
    "construction & engineering": "Industrials",
    "transportation": "Industrials",
    "road & rail": "Industrials",
    "machinery": "Industrials",
    "electrical equipment": "Industrials",
    "commercial & professional services": "Industrials",
    # Utilities (Telecom folds here per TARGET_ALLOCATION)
    "telecommunications": "Utilities",
    "telecom": "Utilities",
    "electric utilities": "Utilities",
    "gas utilities": "Utilities",
    "water utilities": "Utilities",
    "multi-utilities": "Utilities",
    # Materials
    "metals & mining": "Materials",
    "mining": "Materials",
    "chemicals": "Materials",
    "basic materials": "Materials",
    "construction materials": "Materials",
    "paper & forest products": "Materials",
    # Real Estate
    "reits": "Real Estate",
    "reit": "Real Estate",
    "real estate management & development": "Real Estate",
    # Energy
    "oil & gas": "Energy",
    "oil, gas & consumable fuels": "Energy",
    "oil & gas exploration & production": "Energy",
    "oil & gas refining & marketing": "Energy",
    # Bonds / Fixed Income
    "fixed income": "Bonds",
    "bond": "Bonds",
    "bonds": "Bonds",
    # Broad Market Index (index ETFs, multi-sector)
    "index": "Broad Market Index",
    "broad market": "Broad Market Index",
    "etf": "Broad Market Index",
    # Fallback
    "n/a": "Other",
    "unknown": "Other",
    "": "Other",
}


def normalize_sector(raw: str | None) -> str:
    """Return the canonical sector for any raw sector string.

    Canonical strings pass through unchanged.  Known aliases are mapped.
    Anything else returns "Other" — add an entry to _ALIASES to map new
    Finnhub industry strings to the correct canonical bucket.
    """
    if not raw:
        return "Other"
    if raw in CANONICAL_SECTORS:
        return raw
    mapped = _ALIASES.get(raw.lower())
    if mapped:
        return mapped
    return "Other"
