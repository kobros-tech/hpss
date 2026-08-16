"""Run the research-oriented HPSS ablations and control datasets.

Usage:
    python research_benchmark.py

Outputs RESEARCH_RESULTS.csv. The default run uses the repository dictionary,
plus deterministic random-string and structured-identifier controls. A small
sample is used for the synthetic controls so the experiment remains practical
in CI; the sample size is recorded in the output.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from hpss_hash import SELECTION_STRATEGIES
from research_experiments import (
    allocation_ablation,
    collision_group_distribution,
    generate_random_strings,
    generate_structured_identifiers,
    length_buckets,
    strategy_representations,
)

ROOT = Path(__file__).resolve().parent
DICTIONARY = ROOT / "dictionaries" / "words.txt"
OUTPUT = ROOT / "RESEARCH_RESULTS.csv"
K_VALUES = tuple(range(2, 21))
SYNTHETIC_COUNT = 50_000


def load_words(path: Path = DICTIONARY) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        return [line.strip().lower() for line in handle if line.strip()]


def add_selector_rows(rows: list[dict], dataset: str, words: list[str], k: int) -> None:
    representations = strategy_representations(words, k)
    for strategy, values in representations.items():
        counts = collision_group_distribution(values)
        stats = allocation_ablation(words, k)[k // 2] if strategy == "HPSS" else None
        unique = len(set(values))
        rows.append({
            "experiment": "selector",
            "dataset": dataset,
            "k": k,
            "strategy": strategy,
            "front": k // 2 if strategy == "HPSS" else "",
            "back": k - k // 2 if strategy == "HPSS" else "",
            "records": len(words),
            "unique": unique,
            "collision_entries": len(words) - unique,
            "max_group": max([len([x for x in values if x == rep]) for rep in set(values)] or [0]),
            "collision_groups": sum(counts.values()),
            "notes": "balanced HPSS allocation" if stats is not None else "",
        })


def add_allocation_rows(rows: list[dict], dataset: str, words: list[str], k: int) -> None:
    for result in allocation_ablation(words, k):
        rows.append({
            "experiment": "allocation",
            "dataset": dataset,
            "k": result.k,
            "strategy": "ALLOCATION",
            "front": result.front,
            "back": result.back,
            "records": len(words),
            "unique": result.unique,
            "collision_entries": result.collision_entries,
            "max_group": result.max_group,
            "collision_groups": "",
            "notes": "all front/back allocations",
        })


def add_length_rows(rows: list[dict], dataset: str, words: list[str], k: int) -> None:
    for bucket, bucket_words in length_buckets(words).items():
        if len(bucket_words) < 2:
            continue
        reps = strategy_representations(bucket_words, k)
        for strategy, values in reps.items():
            unique = len(set(values))
            rows.append({
                "experiment": "length",
                "dataset": dataset,
                "k": k,
                "strategy": strategy,
                "front": "",
                "back": "",
                "records": len(bucket_words),
                "unique": unique,
                "collision_entries": len(bucket_words) - unique,
                "max_group": max((values.count(value) for value in set(values)), default=0),
                "collision_groups": "",
                "notes": f"length_bucket={bucket}",
            })


def main() -> None:
    datasets = {
        "english-word": load_words(),
        "random-alphanumeric": generate_random_strings(SYNTHETIC_COUNT),
        "structured-identifier": generate_structured_identifiers(SYNTHETIC_COUNT),
    }
    rows: list[dict] = []

    for dataset, words in datasets.items():
        # Allocation ablation is the key research experiment. Use every k on
        # synthetic controls and a representative range on the large dictionary.
        for k in K_VALUES:
            add_allocation_rows(rows, dataset, words, k)
            add_selector_rows(rows, dataset, words, k)

        # Length-stratified analysis is most useful on the natural-language data.
        if dataset == "english-word":
            for k in (4, 8, 12, 16, 20):
                add_length_rows(rows, dataset, words, k)

    fieldnames = [
        "experiment", "dataset", "k", "strategy", "front", "back", "records",
        "unique", "collision_entries", "max_group", "collision_groups", "notes",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUTPUT} with {len(rows):,} rows")
    print("Datasets:", ", ".join(datasets))
    print("k values:", K_VALUES)
    print("Synthetic controls:", SYNTHETIC_COUNT, "records each")


if __name__ == "__main__":
    main()
