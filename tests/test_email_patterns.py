from email_extractor import email_patterns


def test_finds_plain_email():
    matches = email_patterns.find_emails("Reach us at jane.doe@example-company.com today.")
    assert [m["email"] for m in matches] == ["jane.doe@example-company.com"]


def test_finds_bracketed_obfuscation():
    matches = email_patterns.find_emails("Email: john [at] acme [dot] com")
    assert [m["email"] for m in matches] == ["john@acme.com"]


def test_finds_bare_word_obfuscation():
    matches = email_patterns.find_emails("contact jane at acme dot co dot uk for details")
    assert [m["email"] for m in matches] == ["jane@acme.co.uk"]


def test_ignores_asset_filenames():
    matches = email_patterns.find_emails("<img src='photo@2x.png'>")
    assert matches == []


def test_ignores_placeholder_domains():
    matches = email_patterns.find_emails("Contact you@example.com for a demo")
    assert matches == []


def test_deduplicates_case_insensitively():
    matches = email_patterns.find_emails("Mail Jane@Acme.com or jane@acme.com")
    assert len(matches) == 1


def test_role_based_detection():
    assert email_patterns.is_role_based("info@acme.com") is True
    assert email_patterns.is_role_based("support@acme.com") is True
    assert email_patterns.is_role_based("jane.doe@acme.com") is False


def test_context_snippet_captures_surrounding_text():
    text = "Our sales team can be reached at sales@acme.com for pricing questions."
    matches = email_patterns.find_emails(text)
    assert "sales team" in matches[0]["context"]
