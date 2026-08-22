"""Four-way ablation of HPSS Selection and HPSS Hash.

For every dataset, k, and hash function, compare:

A. original input -> standard hash
B. HPSS selection -> standard hash
C. original input -> HPSS Hash
D. HPSS selection -> HPSS Hash

Input normalization is performed once outside the timed section. The timed
pipeline therefore measures hashing alone for A/C and selection + hashing for
B/D. All hash outputs are constrained to 64 bits.
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

from hpss_hash import MASK64, REFERENCE_HASHES, select_hpss
from hpss_hash_experiment import hpss_positional_hash
from research_datasets import load_english_words, load_estonian_domains
from research_experiments import collision_stats

DEFAULT_REPETITIONS = 15
K_VALUES = tuple(range(2, 13))
HashFunction = Callable[[str], int]


def fnv1a64(text: str) -> int:
    return REFERENCE_HASHES["FNV1A64"](text.encode("utf-8")) & MASK64


def murmur3_64(text: str) -> int:
    return REFERENCE_HASHES["MURMUR3_64"](text.encode("utf-8")) & MASK64


def xxhash64(text: str) -> int:
    return REFERENCE_HASHES["XXHASH64"](text.encode("utf-8")) & MASK64


def sha256_64(text: str) -> int:
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[-8:], "big")


def sha3_256_64(text: str) -> int:
    return int.from_bytes(hashlib.sha3_256(text.encode("utf-8")).digest()[-8:], "big")


STANDARD_HASHES: dict[str, HashFunction] = {
    "FNV1A64": fnv1a64,
    "MURMUR3_64": murmur3_64,
    "XXHASH64": xxhash64,
    "SHA256": sha256_64,
    "SHA3_256": sha3_256_64,
}

ALL_HASHES = {**STANDARD_HASHES, "HPSS_POSITIONAL": hpss_positional_hash}


def benchmark_pipeline(
    records: list[str],
    k: int,
    hash_name: str,
    selection: bool,
    repetitions: int,
) -> tuple[dict[str, int | float], dict[str, int | float], float, float, float]:
    """Benchmark one selection/hash configuration."""
    hash_fn = ALL_HASHES[hash_name]
    representations = [select_hpss(value, k) for value in records] if selection else records
    representation_stats = collision_stats(representations)

    timings: list[float] = []
    hashed: list[int] = []
    for _ in range(repetitions):
        start = time.perf_counter_ns()
        hashed = [hash_fn(value) for value in representations]
        timings.append((time.perf_counter_ns() - start) / 1e9)

    median_seconds = statistics.median(timings)
    quartiles = statistics.quantiles(timings, n=4) if len(timings) >= 2 else [median_seconds] * 3
    iqr = quartiles[2] - quartiles[0]
    throughput = len(records) / median_seconds if median_seconds else float("inf")
    return (
        representation_stats,
        collision_stats(hashed),
        median_seconds,
        iqr,
        throughput,
    )


def run(
    datasets: dict[str, list[str]],
    repetitions: int = DEFAULT_REPETITIONS,
) -> list[dict[str, object]]:
    if repetitions < 1:
        raise ValueError("repetitions must be positive")

    rows: list[dict[str, object]] = []
    for dataset_name, raw_records in datasets.items():
        records = [record.lower() for record in raw_records]
        for k in K_VALUES:
            for hash_name in ALL_HASHES:
                for selection in (False, True):
                    effective_hash = hash_name
                    # HPSS_POSITIONAL is the HPSS Hash contribution; standard
                    # hashes are the comparison family. The selection flag is
                    # still recorded for the four-way ablation.
                    (
                        representation_stats,
                        hash_stats,
                        seconds,
                        iqr,
                        throughput,
                    ) = benchmark_pipeline(
                        records, k, effective_hash, selection, repetitions
                    )
                    configuration = (
                        "D" if selection and hash_name == "HPSS_POSITIONAL"
                        else "C" if not selection and hash_name == "HPSS_POSITIONAL"
                        else "B" if selection
                        else "A"
                    )
                    rows.append(
                        {
                            "dataset": dataset_name,
                            "k": k,
                            "configuration": configuration,
                            "selection": "HPSS" if selection else "NONE",
                            "hash": hash_name,
                            "records": len(records),
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
        "random_ascii": _random_ascii_dataset(),
    }
    rows = run(datasets, args.repetitions)
    write_csv(rows, args.output)
    print(f"rows={len(rows)} output={args.output}")


def _random_ascii_dataset(count: int = 50_000, length: int = 12, seed: int = 0) -> list[str]:
    import random
    import string

    rng = random.Random(seed)
    alphabet = string.ascii_lowercase + string.digits
    values: set[str] = set()
    while len(values) < count:
        values.add("".join(rng.choices(alphabet, k=length)))
    return sorted(values)


if __name__ == "__main__":
    main()
