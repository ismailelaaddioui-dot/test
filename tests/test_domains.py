from lead_finder.domains import resolve_domain


def test_known_outlets_resolve():
    assert resolve_domain("Monocle") == "monocle.com"
    assert resolve_domain("Vogue Arabia") == "voguearabia.com"
    assert resolve_domain("Magnum Photos") == "magnumphotos.com"


def test_case_insensitive():
    assert resolve_domain("MONOCLE") == "monocle.com"
    assert resolve_domain("marie claire") == "marieclaire.com"


def test_unknown_returns_empty():
    assert resolve_domain("Some Unknown Studio") == ""
    assert resolve_domain("") == ""


def test_trailing_qualifier_trimmed():
    assert resolve_domain("Monocle Magazine") == "monocle.com"
