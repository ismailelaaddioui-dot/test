#!/usr/bin/env python3
"""Generate queries.txt from role x outlet lists.

Edit the ROLES and the CATEGORIES lists below, then run:

    python generate_queries.py

to regenerate queries.txt. Every query targets LinkedIn profiles:

    site:linkedin.com "<role>" "<outlet>"

Add outlets or roles anytime — the daily job automatically picks up the
larger list on its next rotation.
"""

# Roles applied to every outlet-based category.
ROLES = [
    "photo editor",
    "picture editor",
    "senior photo editor",
    "deputy photo editor",
    "photography editor",
    "photo director",
    "director of photography",
    "head of photography",
    "art director",
    "creative director",
    "visuals editor",
    "image editor",
    "commissioning editor",
    "photo producer",
    "content director",
    "brand photography",
]

# For city-based searches, a tighter role set (cities are noisier).
CITY_ROLES = [
    "photo editor",
    "picture editor",
    "art director",
    "creative director",
    "photo director",
]

# category name -> list of outlets/anchors
CATEGORIES = {
    "Travel & lifestyle magazines": [
        "Condé Nast Traveller", "Condé Nast Traveler", "Travel + Leisure",
        "National Geographic Traveller", "Afar", "Monocle", "Wallpaper",
        "Suitcase", "Departures", "Robb Report", "Lonely Planet",
    ],
    "Fashion & culture magazines": [
        "Vogue", "Harper's Bazaar", "Elle", "Marie Claire", "GQ", "Esquire",
        "Vanity Fair", "W Magazine", "Porter", "i-D", "Dazed", "AnOther",
    ],
    "MENA / Africa titles": [
        "Vogue Arabia", "GQ Middle East", "Harper's Bazaar Arabia",
        "Marie Claire Arabia", "Condé Nast Traveller Middle East", "Brownbook",
        "Nataal", "Something Curated", "Canvas", "Selections", "MILLE",
        "Scoop Empire",
    ],
    "Hospitality & luxury brands": [
        "Aman", "Mandarin Oriental", "Four Seasons", "Belmond", "Rosewood",
        "Six Senses", "Soneva", "Bulgari Hotels", "Ritz-Carlton",
    ],
    "Photo agencies & representation": [
        "Magnum Photos", "VII Photo", "Redux Pictures", "Gallery Stock",
        "Trunk Archive", "Art Partner", "Webber Represents",
    ],
}

# City-based searches use CITY_ROLES instead of the full ROLES list.
CITY_CATEGORY = {
    "City-based (freelancers + smaller regional titles)": [
        "Dubai", "Abu Dhabi", "Doha", "Riyadh", "Cairo", "Beirut", "Lagos",
        "Nairobi", "Marrakech", "Casablanca", "Amman",
    ],
}

# Broad catch-all queries that surface a large pool beyond the named outlets.
CATCH_ALL = [
    'site:linkedin.com "photo editor" "magazine"',
    'site:linkedin.com "picture editor" "magazine"',
]

OUTPUT = "queries.txt"


def _query(role: str, anchor: str) -> str:
    return f'site:linkedin.com "{role}" "{anchor}"'


def build_lines() -> list[str]:
    lines = [
        "# Auto-generated query list - role x outlet combos.",
        "# Regenerate with generate_queries.py after editing the lists.",
        "# One query per line. Lines starting with # are ignored by the tool.",
        "",
    ]
    for category, outlets in CATEGORIES.items():
        lines.append(f"# --- {category} ---")
        for role in ROLES:
            for outlet in outlets:
                lines.append(_query(role, outlet))
        lines.append("")

    for category, cities in CITY_CATEGORY.items():
        lines.append(f"# --- {category} ---")
        for role in CITY_ROLES:
            for city in cities:
                lines.append(_query(role, city))
        lines.append("")

    lines.append("# --- Broad catch-all (large pool) ---")
    lines.extend(CATCH_ALL)
    lines.append("")
    return lines


def main() -> None:
    lines = build_lines()
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    query_count = sum(
        1 for ln in lines if ln.startswith("site:")
    )
    print(f"Wrote {query_count} queries to {OUTPUT}")


if __name__ == "__main__":
    main()
