"""Download deterministic external datasets used by the research benchmark.

The repository stores small provenance manifests rather than large
third-party data blobs. CI downloads pinned upstream files so experiments
remain reproducible without unnecessarily bloating this repository.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DICT = ROOT / "dictionaries"
SAMPLE_SIZE = 50_000

ENGLISH_URL = (
    "https://raw.githubusercontent.com/dwyl/english-words/"
    "20f5cc9b3f0ccc8ce45d814c532b7c2031bba31c/words.txt"
)
DOMAIN_URL = (
    "https://raw.githubusercontent.com/elliotwutingfeng/"
    "EstonianInternetFoundationDomains/"
    "173ba6bfe0c7ca8071594803c3e3f64b7e514e8c/domains.txt"
)


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_english(text: str) -> list[str]:
    values = []
    for line in text.splitlines():
        token = line.strip()
        if token and all(ord(c) < 128 for c in token):
            values.append(token)
    return list(dict.fromkeys(values))


def clean_domains(text: str) -> list[str]:
    values = []
    for line in text.splitlines():
        token = line.strip().lower().rstrip(".")
        if (
            token
            and " " not in token
            and "." in token
            and all(ord(c) < 128 for c in token)
        ):
            values.append(token)
    return list(dict.fromkeys(values))


def write_values(filename: str, values: list[str], *, limit: int | None = None) -> None:
    if limit is not None:
        values = values[:limit]
    if not values:
        raise RuntimeError(f"{filename}: no usable records")
    path = DICT / filename
    path.write_text("\n".join(values) + "\n", encoding="utf-8")
    print(f"Wrote {len(values):,} records to {path}")


def main() -> None:
    DICT.mkdir(exist_ok=True)

    print("Downloading pinned English words.txt...")
    write_values("words.txt", clean_english(fetch_text(ENGLISH_URL)))

    print("Downloading pinned Estonian domains...")
    write_values(
        "estonian_domains.txt",
        clean_domains(fetch_text(DOMAIN_URL)),
        limit=SAMPLE_SIZE,
    )


if __name__ == "__main__":
    main()
