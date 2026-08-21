"""Selection-allocation experiment with a fixed downstream hash.

This experiment isolates the effect of prefix/suffix selection by keeping the
hash function fixed (XXHash64).  The ratio parameter ``alpha`` controls the
prefix allocation under the existing deterministic round-half-up rule:

* alpha=0.0 -> suffix only;
* alpha=0.5 -> balanced prefix/suffix allocation;
* alpha=1.0 -> prefix only.

A no-selection baseline is included for every k.  The experiment records both
representation-level and hash-level collision metrics, plus end-to-end
selection+hash timing.  It intentionally does not compare different hash
functions; that is a later independence experiment.

Usage:
    python research_selection_experiment.py \
        --input dictionaries/words.txt \
        --output results/selection_experiment.csv
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from collections import Counter
from math import floor
from pathlib import Path
from typing import Callable

from hpss_hash import hash_xxhash64, select_hpss_ratio
from research_datasets import load_english_words

DEFAULT_ALPHAS = tuple(i / 10 for i in range(11))
DEFAULT_K_VALUES = tuple(range(2, 13))


def collision_stats(values: list[object]) -> dict[str, int | float]:
    """Return the collision metrics used throughout the research benchmark."""
    n = len(values)
    if not n:
        return {
            "unique": 0,
            "collision_entries": 0,
            "collision_rate": 0.0,
            "collision_pairs": 0,
            "max_group": 0,
        }

    counts = Counter(values)
    unique = len(counts)
    collision_entries = n - unique
    return {
        "unique": unique,
        "collision_entries": collision_entries,
        "collision_rate": collision_entries / n,
        "collision_pairs": sum(
            count * (count - 1) // 2 for count in counts.values() if count > 1
        ),
        "max_group": max(counts.values()),
    }


def ratio_prefix_count(k: int, alpha: float) -> int:
    """Return the nominal prefix allocation for a full k-character budget."""
    if k < 0:
        raise ValueError("k must be non-negative")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be between 0.0 and 1.0")
    return min(k, floor(alpha * k + 0.5))


def select_representation(word: str, k: int, alpha: float | None) -> str:
    """Select a representation, or return the normalized word unchanged."""
    if alpha is None:
        return word
    return select_hpss_ratio(word, k, alpha)


def benchmark_pipeline(
    words: list[str],
    k: int,
    alpha: float | None,
    repeats: int,
    hash_fn: Callable[[bytes], int] = hash_xxhash64,
) -> dict[str, float | int | str | None]:
    """Benchmark one allocation against the fixed XXHash64 pipeline."""
    if repeats < 1:
        raise ValueError("repeats must be positive")

    representations = [select_representation(word, k, alpha) for word in words]
    representation_bytes = [representation.encode("utf-8") for representation in representations]

    representation_stats = collision_stats(representations)
    timings: list[float] = []
    hash_values: list[int] = []

    for _ in range(repeats):
        start = time.perf_counter()
        values = [hash_fn(data) for data in representation_bytes]
        elapsed = time.perf_counter() - start
        timings.append(elapsed)
        hash_values = values

    hash_stats = collision_stats(hash_values)
    median_seconds = statistics.median(timings)
    throughput = len(words) / median_seconds if median_seconds else float("inf")

    prefix = None if alpha is None else ratio_prefix_count(k, alpha)
    suffix = None if prefix is None else k - prefix

    return {
        "selection": "NONE" if alpha is None else "HPSS_RATIO",
        "k": k,
        "alpha": alpha,
        "prefix": prefix,
        "suffix": suffix,
        "words": len(words),
        "hash": "XXHASH64",
        "representation_unique": representation_stats["unique"],
        "representation_collision_entries": representation_stats["collision_entries"],
        "representation_collision_rate": representation_stats["collision_rate"],
        "representation_collision_pairs": representation_stats["collision_pairs"],
        "representation_max_group": representation_stats["max_group"],
        "hash_unique": hash_stats["unique"],
        "hash_collision_entries": hash_stats["collision_entries"],
        "hash_collision_rate": hash_stats["collision_rate"],
        "hash_collision_pairs": hash_stats["collision_pairs"],
        "hash_max_group": hash_stats["max_group"],
        "median_seconds": median_seconds,
        "hashes_per_second": throughput,
    }


def run(
    words: list[str],
    ks: list[int],
    alphas: list[float],
    repeats: int,
) -> list[dict[str, float | int | str | None]]:
    """Run the no-selection baseline and all requested ratio allocations."""
    rows: list[dict[str, float | int | str | None]] = []
    for k in ks:
        if k <= 0:
            continue
        rows.append(benchmark_pipeline(words, k, None, repeats))
        for alpha in alphas:
            rows.append(benchmark_pipeline(words, k, alpha, repeats))
    return rows


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    """Write experiment rows to a reproducible CSV artifact."""
    if not rows:
        raise ValueError("cannot write an empty experiment")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--k-min", type=int, default=2)
    parser.add_argument("--k-max", type=int, default=12)
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument(
        "--alphas",
        type=float,
        nargs="+",
        default=list(DEFAULT_ALPHAS),
        help="prefix allocation ratios in [0, 1] (default: 0.0 through 1.0 by 0.1)",
    )
    args = parser.parse_args()

    if args.k_min < 1 or args.k_max < args.k_min:
        raise SystemExit("invalid k range")
    if args.repeats < 1:
        raise SystemExit("repeats must be positive")
    if any(not 0.0 <= alpha <= 1.0 for alpha in args.alphas):
        raise SystemExit("alpha values must be between 0.0 and 1.0")

    words = load_english_words(args.input)
    if not words:
        raise SystemExit("input dictionary is empty")

    rows = run(
        words,
        list(range(args.k_min, args.k_max + 1)),
        args.alphas,
        args.repeats,
    )
    write_csv(rows, args.output)
    print(f"words={len(words)} rows={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
