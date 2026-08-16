"""Reproducible real-world benchmark for HPSS selection and hashing.

The benchmark reports selection-stage collisions separately from collisions
introduced by each final encoder. Reference hashes are applied to the exact
same UTF-8 representations produced by each selector.
"""

from __future__ import annotations

import csv
import platform
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from hpss_hash import REFERENCE_HASHES, SELECTION_STRATEGIES, CompiledEncoder

ROOT = Path(__file__).resolve().parent
DICTIONARY = ROOT / "dictionaries" / "words.txt"
OUTPUT = ROOT / "RESULTS_fresh.csv"

# Odd values are deliberately included. For odd k, HPSS uses floor(k/2)
# characters from the front and ceil(k/2) from the back; e.g. k=5 => 2+3.
K_VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
REPETITIONS = 5

hpss_encode = CompiledEncoder()


def load_words(path: Path = DICTIONARY) -> list[str]:
    """Load and normalize one key per line."""
    with path.open("r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


def collision_stats(values) -> dict[str, int | float]:
    """Return unique count, collision entries, pairs, and largest group."""
    n = len(values)
    if n == 0:
        return {
            "unique": 0,
            "collision_entries": 0,
            "collision_entry_rate": 0.0,
            "collision_pairs": 0,
            "max_group": 0,
        }
    counts = Counter(values)
    unique = len(counts)
    return {
        "unique": unique,
        "collision_entries": n - unique,
        "collision_entry_rate": (n - unique) / n,
        "collision_pairs": sum(f * (f - 1) // 2 for f in counts.values() if f > 1),
        "max_group": max(counts.values()),
    }


def timeit(fn, items, repetitions: int = REPETITIONS) -> tuple[float, float]:
    """Return median elapsed seconds and items/second."""
    timings = []
    for _ in range(repetitions):
        start = time.perf_counter()
        for item in items:
            fn(item)
        timings.append(time.perf_counter() - start)
    median = statistics.median(timings)
    return median, len(items) / median


def build_row(
    *, k: int, strategy: str, words: int, rep_stats: dict, hash_name: str,
    hash_stats: dict, seconds: float, throughput: float,
) -> dict:
    return {
        "dataset": "dwyl/english-word",
        "k": k,
        "strategy": strategy,
        "words": words,
        "representation_unique": rep_stats["unique"],
        "representation_collision_entries": rep_stats["collision_entries"],
        "representation_collision_rate": rep_stats["collision_entry_rate"],
        "representation_collision_pairs": rep_stats["collision_pairs"],
        "representation_max_group": rep_stats["max_group"],
        "hash": hash_name,
        "hash_unique": hash_stats["unique"],
        "hash_collision_entries": hash_stats["collision_entries"],
        "hash_collision_rate": hash_stats["collision_entry_rate"],
        "hash_collision_pairs": hash_stats["collision_pairs"],
        "hash_max_group": hash_stats["max_group"],
        "median_seconds": seconds,
        "hashes_per_second": throughput,
    }


def main() -> None:
    words = load_words()
    print(f"Loaded {len(words):,} normalized records from {DICTIONARY}")

    rows = []
    for k in K_VALUES:
        for strategy, selector in SELECTION_STRATEGIES.items():
            representations = [selector(word, k) for word in words]
            representation_bytes = [rep.encode("utf-8") for rep in representations]
            rep_stats = collision_stats(representations)

            median, speed = timeit(hpss_encode, representations)
            hpss_values = [hpss_encode(rep) for rep in representations]
            hpss_stats = collision_stats(hpss_values)
            rows.append(build_row(
                k=k, strategy=strategy, words=len(words), rep_stats=rep_stats,
                hash_name="HPSS_POSITIONAL", hash_stats=hpss_stats,
                seconds=median, throughput=speed,
            ))

            for hash_name, hash_fn in REFERENCE_HASHES.items():
                median, speed = timeit(hash_fn, representation_bytes)
                values = [hash_fn(data) for data in representation_bytes]
                stats = collision_stats(values)
                rows.append(build_row(
                    k=k, strategy=strategy, words=len(words), rep_stats=rep_stats,
                    hash_name=hash_name, hash_stats=stats,
                    seconds=median, throughput=speed,
                ))
        print(f"k={k} done")

    fieldnames = list(rows[0])
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "dataset": str(DICTIONARY.relative_to(ROOT)),
        "records": len(words),
        "k_values": ",".join(map(str, K_VALUES)),
        "repetitions": REPETITIONS,
    }
    meta_path = ROOT / "RESULTS_METADATA.txt"
    meta_path.write_text("\n".join(f"{k}={v}" for k, v in metadata.items()) + "\n", encoding="utf-8")

    print(f"Wrote {OUTPUT}")
    print(f"Wrote {meta_path}")


if __name__ == "__main__":
    main()
