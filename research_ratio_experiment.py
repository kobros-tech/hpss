"""Ratio-allocation experiment for HPSS.

This benchmark evaluates every distinct prefix/suffix allocation for each k,
then maps allocations to the alpha values that generate them under the
round-half-up rule. It reports collision statistics and repeated timing
measurements so collision and speed optima can be compared without assuming
that one alpha is universally best.

Usage:
    python research_ratio_experiment.py --input dictionaries/words.txt --output results/ratio_experiment.csv
"""

from __future__ import annotations

import argparse
import csv
import statistics
import time
from collections import Counter
from pathlib import Path

from hpss_hash import select_hpss_ratio


def load_words(path: Path) -> list[str]:
    words = []
    seen = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        word = raw.strip().lower()
        if word and word not in seen:
            seen.add(word)
            words.append(word)
    return words


def alpha_for_allocation(front: int, k: int) -> tuple[float, float]:
    """Return the inclusive alpha interval producing `front` characters.

    With p=floor(alpha*k+0.5), allocation p occurs for
    (p-0.5)/k <= alpha < (p+0.5)/k, clipped to [0,1].
    """
    lo = max(0.0, (front - 0.5) / k)
    hi = min(1.0, (front + 0.5) / k)
    return lo, hi


def collision_stats(representations: list[str]) -> tuple[int, int, int, int]:
    counts = Counter(representations)
    unique = len(counts)
    collision_entries = sum(1 for n in counts.values() if n > 1)
    collision_pairs = sum(n * (n - 1) // 2 for n in counts.values())
    max_group = max(counts.values(), default=0)
    return unique, collision_entries, collision_pairs, max_group


def benchmark_allocation(words: list[str], k: int, front: int, repeats: int) -> dict[str, float | int | str]:
    suffix = k - front
    alpha = front / k
    lo, hi = alpha_for_allocation(front, k)

    # Time selection separately from collision accounting.
    timings = []
    reps = None
    for _ in range(repeats):
        start = time.perf_counter_ns()
        reps = [select_hpss_ratio(word, k, alpha) for word in words]
        elapsed = time.perf_counter_ns() - start
        timings.append(elapsed / 1e9)

    assert reps is not None
    unique, collision_entries, collision_pairs, max_group = collision_stats(reps)
    median_seconds = statistics.median(timings)
    throughput = len(words) / median_seconds if median_seconds else float("inf")

    return {
        "k": k,
        "front": front,
        "suffix": suffix,
        "alpha": alpha,
        "alpha_interval_low": lo,
        "alpha_interval_high": hi,
        "unique": unique,
        "collision_entries": collision_entries,
        "collision_rate": collision_entries / len(words) if words else 0.0,
        "collision_pairs": collision_pairs,
        "max_group": max_group,
        "median_seconds": median_seconds,
        "throughput_words_per_second": throughput,
    }


def run(words: list[str], ks: list[int], repeats: int) -> list[dict[str, object]]:
    rows = []
    for k in ks:
        if k <= 0:
            continue
        for front in range(k + 1):
            rows.append(benchmark_allocation(words, k, front, repeats))
    return rows


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--k-min", type=int, default=2)
    parser.add_argument("--k-max", type=int, default=12)
    parser.add_argument("--repeats", type=int, default=7)
    args = parser.parse_args()

    if args.k_min < 1 or args.k_max < args.k_min:
        raise SystemExit("invalid k range")
    if args.repeats < 1:
        raise SystemExit("repeats must be positive")

    words = load_words(args.input)
    if not words:
        raise SystemExit("input dictionary is empty")

    rows = run(words, list(range(args.k_min, args.k_max + 1)), args.repeats)
    write_csv(rows, args.output)
    print(f"words={len(words)} allocations={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
