"""Regex-based email discovery, de-obfuscation, and validation.

Handles both plain "name@domain.com" addresses and common human-readable
obfuscations such as "name [at] domain [dot] com" that site owners use to
dodge naive scrapers.
"""

import re

# Standard, reasonably strict email pattern (local part + domain + TLD).
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# Bracketed/parenthesized obfuscation of "@" and "." are unambiguous, so we
# can safely normalize them anywhere in the text before running EMAIL_RE.
_BRACKETED_AT = re.compile(r"\s*[\(\[\{<]\s*at\s*[\)\]\}>]\s*", re.IGNORECASE)
_BRACKETED_DOT = re.compile(r"\s*[\(\[\{<]\s*dot\s*[\)\]\}>]\s*", re.IGNORECASE)

# Bare-word obfuscation ("name at domain dot com") is ambiguous in general
# text, so it is matched as one whole pattern rather than by blind
# word-for-symbol substitution (which would corrupt unrelated sentences).
_BARE_OBFUSCATED_RE = re.compile(
    r"\b([a-zA-Z0-9._%+-]+)\s+at\s+"
    r"([a-zA-Z0-9-]+(?:\s+dot\s+[a-zA-Z0-9-]+)+)\b",
    re.IGNORECASE,
)

# Domains/TLDs that are almost always false positives: placeholder emails
# in boilerplate, or asset filenames like "photo@2x.png" that the plain
# regex would otherwise mistake for a TLD.
_NON_EMAIL_TLDS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp", "tiff",
    "css", "js", "json", "woff", "woff2", "ttf", "eot", "map",
}
_PLACEHOLDER_DOMAINS = {
    "example.com", "example.org", "example.net", "domain.com",
    "yourdomain.com", "email.com", "test.com", "sentry.io",
    "wixpress.com", "godaddy.com", "asdf.com",
}

# Local-part prefixes that indicate a shared/role mailbox rather than a
# named individual.
ROLE_PREFIXES = {
    "info", "sales", "support", "contact", "admin", "help", "office",
    "hello", "service", "careers", "jobs", "hr", "press", "media",
    "marketing", "billing", "accounts", "enquiries", "inquiries",
    "webmaster", "noreply", "no-reply", "team", "general", "reception",
}

CONTEXT_RADIUS = 60  # characters of surrounding text to keep as a snippet


def normalize_obfuscation(text: str) -> str:
    """Turn unambiguous bracketed obfuscations into real '@'/'.' characters."""
    text = _BRACKETED_AT.sub("@", text)
    text = _BRACKETED_DOT.sub(".", text)
    return text


def _bare_obfuscated_matches(text: str) -> list[tuple[str, int, int]]:
    """Find 'name at domain dot com' style addresses.

    Returns (reconstructed_email, start, end) so callers can still pull a
    context snippet from the original text.
    """
    results = []
    for match in _BARE_OBFUSCATED_RE.finditer(text):
        local, domain_words = match.group(1), match.group(2)
        domain = re.sub(r"\s+dot\s+", ".", domain_words, flags=re.IGNORECASE)
        results.append((f"{local}@{domain}", match.start(), match.end()))
    return results


def is_probably_valid(email: str) -> bool:
    """Filter out syntactically-valid but semantically bogus matches."""
    email = email.strip().strip(".,;:")
    if "@" not in email:
        return False
    local, _, domain = email.rpartition("@")
    if not local or not domain:
        return False
    domain = domain.lower()
    if domain in _PLACEHOLDER_DOMAINS:
        return False
    tld = domain.rsplit(".", 1)[-1]
    if tld in _NON_EMAIL_TLDS:
        return False
    if len(domain) > 253 or len(local) > 64:
        return False
    return True


def is_role_based(email: str) -> bool:
    """True if the local part looks like a shared team mailbox."""
    local = email.split("@", 1)[0].lower()
    local = re.split(r"[._+-]", local)[0]
    return local in ROLE_PREFIXES


def find_emails(text: str) -> list[dict]:
    """Extract every plausible email address from a block of text.

    Returns a list of dicts: {"email": str, "context": str}, deduplicated
    by lowercased address (first occurrence's context wins).
    """
    normalized = normalize_obfuscation(text)
    found: dict[str, str] = {}

    for match in EMAIL_RE.finditer(normalized):
        email = match.group(0)
        if not is_probably_valid(email):
            continue
        key = email.lower()
        if key not in found:
            start = max(0, match.start() - CONTEXT_RADIUS)
            end = min(len(normalized), match.end() + CONTEXT_RADIUS)
            found[key] = normalized[start:end].strip()

    # Bare "at"/"dot" obfuscation is scanned on the *original* text since
    # normalization above doesn't touch unbracketed words.
    for email, start, end in _bare_obfuscated_matches(text):
        if not is_probably_valid(email):
            continue
        key = email.lower()
        if key not in found:
            ctx_start = max(0, start - CONTEXT_RADIUS)
            ctx_end = min(len(text), end + CONTEXT_RADIUS)
            found[key] = text[ctx_start:ctx_end].strip()

    return [{"email": email, "context": ctx} for email, ctx in found.items()]
