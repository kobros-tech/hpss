"""Evaluate HPSS selection independently of the downstream hash function.

For each k, the same representations are passed to HPSS positional hashing
and several fixed-width reference hashes. The experiment compares the
original input (no selection) with the existing HPSS balanced selector and
keeps selection identical across hash functions.

The collision metrics are exact for the supplied finite dataset. Timing is
repeated and reported as median seconds and hashes per second.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import statistics
import time
from collections import Counter
from pathlib import Path
from typing import Callable

from hpss_hash import REFERENCE_HASHES, SELECTION_STRATEGIES, CompiledEncoder
from research_datasets import load_english_words

DEFAULT_K_VALUES = tuple(range(2, 13))
DEFAULT_REPETITIONS = 5

HashFunction = Callable[[bytes], int]


def sha256(data: bytes) -> int:
    return int.from_bytes(hashlib.sha256(data).digest(), "big")


def sha3_256(data: bytes) -> int:
    return int.from_bytes(hashlib.sha3_256(data).digest(), "big")


HASH_FUNCTIONS: dict[str, HashFunction] = {
    "HPSS_POSITIONAL": CompiledEncoder(),
    **REFERENCE_HASHES,
    "SHA256": sha256,
    "SHA3_256": sha3_256,
}

SELECTIONS: dict[str, Callable[[str, int], str] | None] = {
    "NONE": None,
    **SELECTION_STRATEGIES,
}


def collision_stats(values: list[int | str]) -> dict[str, int | float]:
    counts = Counter(values)
    n = len(values)
    unique = len(counts)
    collision_entries = n - unique
    return {
        "unique": unique,
        "collision_entries": collision_entries,
        "collision_rate": collision_entries / n if n else 0.0,
        "collision_pairs": sum(n * (n - 1) // 2 for n in counts.values() if n > 1),
        "max_group": max(counts.values(), default=0),
    }


def benchmark_hash(
    hash_fn: HashFunction,
    values: list[bytes],
    repetitions: int,
) -> tuple[dict[str, int | float], float, float]:
    timings: list[float] = []
    hashed: list[int] = []
    for _ in range(repetitions):
        start = time.perf_counter()
        hashed = [hash_fn(value) for value in values]
        timings.append(time.perf_counter() - start)

    median_seconds = statistics.median(timings)
    throughput = len(values) / median_seconds if median_seconds else float("inf")
    return collision_stats(hashed), median_seconds, throughput


def run(words: list[str], k_values: list[int], repetitions: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for k in k_values:
        for selection_name, selector in SELECTIONS.items():
            if selector is None:
                representations = words
            else:
                representations = [selector(word, k) for word in words]

            representation_stats = collision_stats(representations)
            representation_bytes = [value.encode("utf-8") for value in representations]

            for hash_name, hash_fn in HASH_FUNCTIONS.items():
                hash_stats, seconds, throughput = benchmark_hash(
                    hash_fn, representation_bytes, repetitions
                )
                rows.append(
                    {
                        "dataset": "dwyl/english-word",
                        "k": k,
                        "selection": selection_name,
                        "words": len(words),
                        "representation_unique": representation_stats["unique"],
                        "representation_collision_entries": representation_stats["collision_entries"],
                        "representation_collision_rate": representation_stats["collision_rate"],
                        "representation_collision_pairs": representation_stats["collision_pairs"],
                        "representation_max_group": representation_stats["max_group"],
                        "hash": hash_name,
                        "hash_unique": hash_stats["unique"],
                        "hash_collision_entries": hash_stats["collision_entries"],
                        "hash_collision_rate": hash_stats["collision_rate"],
                        "hash_collision_pairs": hash_stats["collision_pairs"],
                        "hash_max_group": hash_stats["max_group"],
                        "median_seconds": seconds,
                        "hashes_per_second": throughput,
                        "timing_repetitions": repetitions,
                    }
                )
        print(f"k={k} done")
    return rows


def write_csv(rows: list[dict[str, object]], output: Path) -> None:
    if not rows:
        raise ValueError("no results")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--k-min", type=int, default=2)
    parser.add_argument("--k-max", type=int, default=12)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    args = parser.parse_args()

    if args.k_min < 1 or args.k_max < args.k_min:
        raise SystemExit("invalid k range")
    if args.repetitions < 1:
        raise SystemExit("repetitions must be positive")

    words = load_english_words(args.input)
    if not words:
        raise SystemExit("input dataset is empty")

    rows = run(words, list(range(args.k_min, args.k_max + 1)), args.repetitions)
    write_csv(rows, args.output)
    print(f"words={len(words)} rows={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
