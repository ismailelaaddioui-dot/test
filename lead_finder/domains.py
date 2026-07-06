"""Map an outlet/company name to its website domain.

Most target outlets are known brands, so a seeded lookup keeps domain
resolution instant and free (no extra search-API calls). Unknown companies
(e.g. results from city-based queries) fall back to an empty string, which
you can fill in by hand in the Sheet or by extending OUTLET_DOMAINS below.
"""

# Canonical outlet name (lowercased) -> primary website domain.
OUTLET_DOMAINS = {
    # Travel & lifestyle
    "condé nast traveller": "cntraveller.com",
    "conde nast traveller": "cntraveller.com",
    "condé nast traveler": "cntraveler.com",
    "conde nast traveler": "cntraveler.com",
    "travel + leisure": "travelandleisure.com",
    "national geographic traveller": "natgeotraveller.co.uk",
    "afar": "afar.com",
    "monocle": "monocle.com",
    "wallpaper": "wallpaper.com",
    "suitcase": "suitcasemag.com",
    "departures": "departures.com",
    "robb report": "robbreport.com",
    "lonely planet": "lonelyplanet.com",
    # Fashion & culture
    "vogue": "vogue.com",
    "harper's bazaar": "harpersbazaar.com",
    "harpers bazaar": "harpersbazaar.com",
    "elle": "elle.com",
    "marie claire": "marieclaire.com",
    "gq": "gq.com",
    "esquire": "esquire.com",
    "vanity fair": "vanityfair.com",
    "w magazine": "wmagazine.com",
    "porter": "net-a-porter.com",
    "i-d": "i-d.co",
    "dazed": "dazeddigital.com",
    "another": "anothermag.com",
    "anothermag": "anothermag.com",
    # MENA / Africa
    "vogue arabia": "voguearabia.com",
    "gq middle east": "gqmiddleeast.com",
    "harper's bazaar arabia": "harpersbazaararabia.com",
    "harpers bazaar arabia": "harpersbazaararabia.com",
    "marie claire arabia": "marieclairearabia.com",
    "condé nast traveller middle east": "cntravellerme.com",
    "conde nast traveller middle east": "cntravellerme.com",
    "brownbook": "brownbook.tv",
    "nataal": "nataal.com",
    "something curated": "somethingcurated.com",
    "canvas": "canvas.art",
    "selections": "selectionsarts.com",
    "mille": "milleworld.com",
    "scoop empire": "scoopempire.com",
    # Hospitality & luxury
    "aman": "aman.com",
    "mandarin oriental": "mandarinoriental.com",
    "four seasons": "fourseasons.com",
    "belmond": "belmond.com",
    "rosewood": "rosewoodhotels.com",
    "six senses": "sixsenses.com",
    "soneva": "soneva.com",
    "bulgari hotels": "bulgarihotels.com",
    "ritz-carlton": "ritzcarlton.com",
    "ritz carlton": "ritzcarlton.com",
    # Photo agencies & representation
    "magnum photos": "magnumphotos.com",
    "vii photo": "viiphoto.com",
    "redux pictures": "reduxpictures.com",
    "gallery stock": "gallerystock.com",
    "trunk archive": "trunkarchive.com",
    "art partner": "artpartner.com",
    "webber represents": "webberrepresents.com",
}


def resolve_domain(company: str) -> str:
    """Best-effort website domain for a company/outlet name ('' if unknown)."""
    if not company:
        return ""
    key = company.strip().lower()
    if key in OUTLET_DOMAINS:
        return OUTLET_DOMAINS[key]
    # Tolerate trailing qualifiers like "Magazine"/"Media" on the company name.
    for suffix in (" magazine", " media", " group", " hotels"):
        if key.endswith(suffix):
            trimmed = key[: -len(suffix)].strip()
            if trimmed in OUTLET_DOMAINS:
                return OUTLET_DOMAINS[trimmed]
    return ""
