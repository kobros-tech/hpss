from pathlib import Path

from research_datasets import load_ascii_records


def test_canonical_loader_normalizes_and_deduplicates(tmp_path: Path):
    source = tmp_path / "records.txt"
    source.write_text(" Alpha \nalpha\nBETA\nβeta\n\n", encoding="utf-8")
    assert load_ascii_records(source) == ["alpha", "beta"]


def test_canonical_loader_preserves_first_seen_order(tmp_path: Path):
    source = tmp_path / "records.txt"
    source.write_text("Zed\nalpha\nzed\nBeta\n", encoding="utf-8")
    assert load_ascii_records(source) == ["zed", "alpha", "beta"]
