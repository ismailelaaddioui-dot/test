from pathlib import Path

from email_extractor.extractor import ExtractionPipeline


def test_ingest_text_deduplicates_across_sources():
    pipeline = ExtractionPipeline()
    pipeline.ingest_text("Contact jane@acme.com for sales", "page-a")
    pipeline.ingest_text("Also reach Jane@Acme.com here", "page-b")

    records = pipeline.records()
    assert len(records) == 1
    assert records[0].email == "jane@acme.com"
    assert {m.origin for m in records[0].mentions} == {"page-a", "page-b"}


def test_ingest_file_records_skip_on_parse_error(tmp_path: Path):
    pipeline = ExtractionPipeline()
    bogus = tmp_path / "broken.pdf"
    bogus.write_bytes(b"not a real pdf")

    pipeline.ingest_file(bogus)

    assert pipeline.records() == []
    assert len(pipeline.skipped()) == 1
    assert "broken.pdf" in pipeline.skipped()[0].source


def test_role_based_flag_propagates():
    pipeline = ExtractionPipeline()
    pipeline.ingest_text("Email support@acme.com or jane.doe@acme.com", "src")
    records = {r.email: r for r in pipeline.records()}
    assert records["support@acme.com"].is_role_based is True
    assert records["jane.doe@acme.com"].is_role_based is False
