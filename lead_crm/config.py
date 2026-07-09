"""Lane definitions: target titles and companies, plus the Morocco rule.

Edit these lists to steer discovery. Each company carries a country and a
flag for whether it's a Morocco production/fixer shop (the one Moroccan
exception that is NOT excluded, because those budgets are international).
"""

from dataclasses import dataclass

# --- Target job titles per lane ------------------------------------------

LANE1_TITLES = [
    "Producer", "Creative Producer", "Senior Producer", "Head of Production",
    "Production Manager", "Head of Content", "Content Director", "Art Buyer",
    "Art Producer",
]

LANE2_TITLES = [
    "Art Buyer", "Head of Content", "Content Manager", "Brand Manager",
    "Creative Director", "Marketing Director",
]

LANE3_TITLES = [
    "Photo Editor", "Deputy Photo Editor", "Visuals Director",
    "Director of Photography", "Photo Researcher",
]


@dataclass(frozen=True)
class Company:
    name: str
    lane: str            # 1A / 1B / 1C / 2 / 3
    country: str
    site: str = ""       # full https:// URL to the company site
    is_morocco_fixer: bool = False  # Moroccan production/fixer -> allowed


# --- Company targets ------------------------------------------------------
# Lane 1A: roster-model production networks
# Lane 1B: hospitality/travel content agencies
# Lane 1C: ad agency art-buying departments
COMPANIES = [
    # 1A
    Company("Raccoon London", "1A", "UK", "https://www.raccoon.london"),
    Company("North Six", "1A", "US", "https://www.northsix.com"),
    Company("Factor Fifty", "1A", "UK", "https://www.factorfifty.com"),
    Company("Production Paradise", "1A", "UK", "https://www.productionparadise.com"),
    Company("Le Book", "1A", "US", "https://www.lebook.com"),
    # 1B
    Company("Studio Black Tomato", "1B", "UK", "https://www.studioblacktomato.com"),
    Company("80 DAYS", "1B", "UK", "https://www.eightydays.me"),
    Company("Spherical", "1B", "UK", "https://www.spherical.co"),
    Company("Mason Circle", "1B", "UK", "https://www.masoncircle.com"),
    Company("Imperial Leisure", "1B", "UK", "https://www.imperialleisure.com"),
    Company("mr.h", "1B", "UK", "https://www.mrh.agency"),
    Company("Sparkloft Media", "1B", "US", "https://www.sparkloftmedia.com"),
    Company("VERB", "1B", "US", "https://www.verbinteractive.com"),
    # 1C
    Company("Wieden+Kennedy", "1C", "UK", "https://www.wk.com"),
    Company("Mother", "1C", "UK", "https://www.motherlondon.com"),
    Company("BBH", "1C", "UK", "https://www.bartleboglehegarty.com"),
    Company("adam&eveDDB", "1C", "UK", "https://www.adamandeveddb.com"),
    Company("Droga5", "1C", "US", "https://www.droga5.com"),
    Company("AMV BBDO", "1C", "UK", "https://www.amvbbdo.com"),
    Company("Ogilvy", "1C", "UK", "https://www.ogilvy.com"),
    Company("We Are Social", "1C", "UK", "https://wearesocial.com"),
    Company("BETC", "1C", "France", "https://www.betc.com"),
    Company("Publicis", "1C", "France", "https://www.publicis.com"),
    Company("Marcel", "1C", "France", "https://www.marcelww.com"),
]


def site_for_company(name: str) -> str:
    """Look up the known site URL for a company name ('' if unknown)."""
    for c in COMPANIES:
        if c.name.lower() == name.strip().lower():
            return c.site
    return ""


def titles_for_lane(lane: str) -> list[str]:
    """Title list for a lane code (1A/1B/1C share Lane 1 titles)."""
    if lane.startswith("1"):
        return LANE1_TITLES
    if lane == "2":
        return LANE2_TITLES
    if lane == "3":
        return LANE3_TITLES
    return []


def is_excluded_client(country: str, is_morocco_fixer: bool) -> bool:
    """True if a company must be excluded as a client.

    Moroccan companies are excluded (local budgets), EXCEPT Morocco
    production/fixer shops, whose clients pay international rates.
    """
    if country.strip().lower() in ("morocco", "ma", "maroc"):
        return not is_morocco_fixer
    return False
