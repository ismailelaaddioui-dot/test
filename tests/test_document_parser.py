from pathlib import Path

import pytest

from email_extractor import document_parser


def test_parse_txt(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("Contact: jane@acme.com")
    assert "jane@acme.com" in document_parser.parse_txt(path)


def test_parse_csv(tmp_path: Path):
    path = tmp_path / "contacts.csv"
    path.write_text("name,email\nJane,jane@acme.com\n")
    text = document_parser.parse_csv(path)
    assert "jane@acme.com" in text


def test_parse_file_dispatches_by_extension(tmp_path: Path):
    path = tmp_path / "a.txt"
    path.write_text("hello@world.com")
    assert "hello@world.com" in document_parser.parse_file(path)


def test_parse_file_unsupported_extension(tmp_path: Path):
    path = tmp_path / "a.xyz"
    path.write_text("nope")
    with pytest.raises(document_parser.DocumentParseError):
        document_parser.parse_file(path)


def test_parse_txt_missing_file_raises(tmp_path: Path):
    with pytest.raises(document_parser.DocumentParseError):
        document_parser.parse_txt(tmp_path / "missing.txt")
