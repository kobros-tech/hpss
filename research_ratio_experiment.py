"""Ratio-allocation experiment for HPSS.

For each character budget k, this benchmark evaluates every distinct
prefix/suffix allocation. Collision metrics are exact for the supplied
finite dataset; timing is repeated and summarized with bootstrap confidence
intervals because runtime is noisy.

Usage:
    python research_ratio_experiment.py --input dictionaries/words.txt \
        --output results/ratio_experiment.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import statistics
import time
from collections import Counter
from pathlib import Path

from hpss_hash import select_hpss_ratio

DEFAULT_BOOTSTRAPS = 2000


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
    """Return the inclusive alpha interval producing `front` characters."""
    if k <= 0:
        raise ValueError("k must be positive")
    if not 0 <= front <= k:
        raise ValueError("front must be between 0 and k")
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


def percentile(values: list[float], probability: float) -> float:
    """Linear-interpolated percentile for a non-empty sample."""
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def bootstrap_ci(
    samples: list[float],
    statistic,
    *,
    iterations: int = DEFAULT_BOOTSTRAPS,
    seed: int = 0,
) -> tuple[float, float]:
    """Return a deterministic percentile-bootstrap 95% confidence interval."""
    if not samples:
        return 0.0, 0.0
    if len(samples) == 1:
        value = statistic(samples)
        return value, value
    rng = random.Random(seed)
    estimates = []
    n = len(samples)
    for _ in range(iterations):
        resample = [samples[rng.randrange(n)] for _ in range(n)]
        estimates.append(float(statistic(resample)))
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def benchmark_allocation(
    words: list[str],
    k: int,
    front: int,
    repeats: int,
    bootstrap_iterations: int = DEFAULT_BOOTSTRAPS,
) -> dict[str, float | int | str]:
    """Measure one discrete allocation and quantify timing uncertainty."""
    if repeats < 1:
        raise ValueError("repeats must be positive")
    if bootstrap_iterations < 1:
        raise ValueError("bootstrap_iterations must be positive")

    suffix = k - front
    alpha = front / k
    lo, hi = alpha_for_allocation(front, k)

    timings: list[float] = []
    reps: list[str] | None = None
    for _ in range(repeats):
        start = time.perf_counter_ns()
        reps = [select_hpss_ratio(word, k, alpha) for word in words]
        elapsed = time.perf_counter_ns() - start
        timings.append(elapsed / 1e9)

    assert reps is not None
    unique, collision_entries, collision_pairs, max_group = collision_stats(reps)
    median_seconds = statistics.median(timings)
    throughput_samples = [len(words) / seconds for seconds in timings if seconds > 0]
    throughput = len(words) / median_seconds if median_seconds else float("inf")
    timing_ci_low, timing_ci_high = bootstrap_ci(
        timings, statistics.median, iterations=bootstrap_iterations, seed=k * 1000 + front
    )
    throughput_ci_low, throughput_ci_high = bootstrap_ci(
        throughput_samples,
        statistics.median,
        iterations=bootstrap_iterations,
        seed=10_000 + k * 1000 + front,
    )
    timing_iqr = (
        statistics.quantiles(timings, n=4)[2] - statistics.quantiles(timings, n=4)[0]
        if len(timings) >= 2
        else 0.0
    )

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
        "timing_iqr_seconds": timing_iqr,
        "timing_ci95_low": timing_ci_low,
        "timing_ci95_high": timing_ci_high,
        "throughput_words_per_second": throughput,
        "throughput_ci95_low": throughput_ci_low,
        "throughput_ci95_high": throughput_ci_high,
        "timing_repeats": repeats,
    }


def run(
    words: list[str],
    ks: list[int],
    repeats: int,
    bootstrap_iterations: int = DEFAULT_BOOTSTRAPS,
) -> list[dict[str, object]]:
    rows = []
    for k in ks:
        if k <= 0:
            continue
        for front in range(k + 1):
            rows.append(benchmark_allocation(words, k, front, repeats, bootstrap_iterations))
    return rows


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    if not rows:
        raise ValueError("no rows to write")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
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
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--bootstrap-iterations", type=int, default=DEFAULT_BOOTSTRAPS)
    args = parser.parse_args()

    if args.k_min < 1 or args.k_max < args.k_min:
        raise SystemExit("invalid k range")
    if args.repeats < 1:
        raise SystemExit("repeats must be positive")
    if args.bootstrap_iterations < 1:
        raise SystemExit("bootstrap iterations must be positive")

    words = load_words(args.input)
    if not words:
        raise SystemExit("input dictionary is empty")

    rows = run(words, list(range(args.k_min, args.k_max + 1)), args.repeats, args.bootstrap_iterations)
    write_csv(rows, args.output)
    print(f"words={len(words)} allocations={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
