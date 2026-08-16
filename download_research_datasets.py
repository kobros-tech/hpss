"""Download deterministic external datasets used by the research benchmark.

The repository stores provenance manifests rather than large third-party data
blobs. CI downloads a fixed prefix from the source so experiments remain
reproducible without unnecessarily vendoring a large upstream file.
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DICT = ROOT / "dictionaries"
SAMPLE_SIZE = 50_000

SOURCES = {
    "estonian_domains.txt": (
        "https://raw.githubusercontent.com/elliotwutingfeng/EstonianInternetFoundationDomains/173ba6bfe0c7ca8071594803c3e3f64b7e514e8c/domains.txt",
        "domain",
    ),
}


def clean_lines(text: str, kind: str) -> list[str]:
    result: list[str] = []
    for line in text.splitlines():
        token = line.strip()
        if not token or token.startswith("#"):
            continue
        if kind == "domain":
            token = token.lower().rstrip(".")
            # Keep only ASCII domains for the primary HPSS study.
            if token and " " not in token and "." in token and all(ord(c) < 128 for c in token):
                result.append(token)
    return list(dict.fromkeys(result))


def download_sample(filename: str, url: str, kind: str) -> None:
    print(f"Downloading {kind} dataset from pinned source commit...")
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8", errors="replace")
    values = clean_lines(text, kind)[:SAMPLE_SIZE]
    if len(values) < SAMPLE_SIZE:
        raise RuntimeError(f"{filename}: only found {len(values)} usable records")
    path = DICT / filename
    path.write_text("\n".join(values) + "\n", encoding="utf-8")
    print(f"Wrote {len(values):,} records to {path}")


if __name__ == "__main__":
    DICT.mkdir(exist_ok=True)
    for filename, (url, kind) in SOURCES.items():
        download_sample(filename, url, kind)
