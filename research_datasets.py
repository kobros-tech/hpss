"""Canonical dataset loading and normalization for HPSS experiments."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DICTIONARIES = ROOT / "dictionaries"
ENGLISH_WORDS = DICTIONARIES / "words.txt"
ESTONIAN_DOMAINS = DICTIONARIES / "estonian_domains.txt"


def normalize_ascii_records(lines: list[str]) -> list[str]:
    """Normalize records exactly once for every benchmark.

    The primary study is ASCII-only. Records are stripped, lower-cased,
    non-empty, ASCII-validated, and de-duplicated while preserving order.
    """
    result: list[str] = []
    seen: set[str] = set()
    for line in lines:
        value = line.strip().lower()
        if not value or any(ord(c) >= 128 for c in value):
            continue
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def load_ascii_records(path: Path) -> list[str]:
    """Load one canonical ASCII record per line."""
    with path.open("r", encoding="utf-8") as f:
        return normalize_ascii_records(f.readlines())


def load_english_words(path: Path = ENGLISH_WORDS) -> list[str]:
    return load_ascii_records(path)


def load_estonian_domains(path: Path = ESTONIAN_DOMAINS) -> list[str]:
    return load_ascii_records(path)
