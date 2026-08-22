"""Evaluate HPSS Hash independently of HPSS Selection.

Every hash function receives the original normalized input directly. This
isolates the contribution of the proposed HPSS positional hash from the
selection layer evaluated in PRs #10-#12.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import random
import statistics
import string
import time
from collections import Counter
from pathlib import Path
from typing import Callable

from hpss_hash import CompiledEncoder, REFERENCE_HASHES
from research_datasets import load_english_words, load_estonian_domains

DEFAULT_REPETITIONS = 15
RANDOM_SEED = 0
RANDOM_COUNT = 50_000
RANDOM_LENGTH = 12

HashFunction = Callable[[bytes], int]
hpss_encoder = CompiledEncoder()


def hpss_positional_hash(data: bytes) -> int:
    return hpss_encoder(data.decode("utf-8"))


def sha256(data: bytes) -> int:
    return int.from_bytes(hashlib.sha256(data).digest(), "big")


def sha3_256(data: bytes) -> int:
    return int.from_bytes(hashlib.sha3_256(data).digest(), "big")


HASH_FUNCTIONS: dict[str, HashFunction] = {
    "HPSS_POSITIONAL": hpss_positional_hash,
    **REFERENCE_HASHES,
    "SHA256": sha256,
    "SHA3_256": sha3_256,
}


def make_random_ascii_dataset(
    count: int = RANDOM_COUNT,
    length: int = RANDOM_LENGTH,
    seed: int = RANDOM_SEED,
) -> list[str]:
    """Generate a reproducible dataset of unique random ASCII strings."""
    if count < 1 or length < 1:
        raise ValueError("count and length must be positive")
    rng = random.Random(seed)
    alphabet = string.ascii_lowercase + string.digits
    values: set[str] = set()
    while len(values) < count:
        values.add("".join(rng.choices(alphabet, k=length)))
    return sorted(values)


def collision_stats(values: list[int]) -> dict[str, int | float]:
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
) -> tuple[dict[str, int | float], float, float, float]:
    timings: list[float] = []
    hashed: list[int] = []
    for _ in range(repetitions):
        start = time.perf_counter_ns()
        hashed = [hash_fn(value) for value in values]
        timings.append((time.perf_counter_ns() - start) / 1e9)

    median_seconds = statistics.median(timings)
    iqr = (
        statistics.quantiles(timings, n=4)[2] - statistics.quantiles(timings, n=4)[0]
        if len(timings) >= 2
        else 0.0
    )
    throughput = len(values) / median_seconds if median_seconds else float("inf")
    return collision_stats(hashed), median_seconds, iqr, throughput


def run(
    datasets: dict[str, list[str]],
    repetitions: int = DEFAULT_REPETITIONS,
) -> list[dict[str, object]]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")

    rows: list[dict[str, object]] = []
    for dataset_name, records in datasets.items():
        values = [record.encode("utf-8") for record in records]
        for hash_name, hash_fn in HASH_FUNCTIONS.items():
            stats, seconds, iqr, throughput = benchmark_hash(hash_fn, values, repetitions)
            rows.append(
                {
                    "dataset": dataset_name,
                    "records": len(records),
                    "hash": hash_name,
                    "unique": stats["unique"],
                    "collision_entries": stats["collision_entries"],
                    "collision_rate": stats["collision_rate"],
                    "collision_pairs": stats["collision_pairs"],
                    "max_group": stats["max_group"],
                    "median_seconds": seconds,
                    "timing_iqr_seconds": iqr,
                    "hashes_per_second": throughput,
                    "timing_repetitions": repetitions,
                }
            )
        print(f"dataset={dataset_name} records={len(records)} done")
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
    parser.add_argument("--english", type=Path, default=Path("dictionaries/words.txt"))
    parser.add_argument("--estonian", type=Path, default=Path("dictionaries/estonian_domains.txt"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    args = parser.parse_args()

    if args.repetitions < 1:
        raise SystemExit("repetitions must be positive")

    datasets = {
        "english_words": load_english_words(args.english),
        "estonian_domains": load_estonian_domains(args.estonian),
        "random_ascii": make_random_ascii_dataset(),
    }
    rows = run(datasets, args.repetitions)
    write_csv(rows, args.output)
    print(f"rows={len(rows)} output={args.output}")


if __name__ == "__main__":
    main()
