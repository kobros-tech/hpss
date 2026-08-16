"""Run the research-oriented HPSS ablations and control datasets.

Usage:
    python research_benchmark.py

Outputs RESEARCH_RESULTS.csv. The default run uses the repository dictionary,
plus deterministic random-string and structured-identifier controls.
"""

from __future__ import annotations

import csv
from pathlib import Path

from research_experiments import (
    allocation_ablation,
    collision_group_distribution,
    collision_stats,
    generate_random_strings,
    generate_structured_identifiers,
    length_buckets,
    strategy_representations,
)

ROOT = Path(__file__).resolve().parent
DICTIONARY = ROOT / "dictionaries" / "words.txt"
OUTPUT = ROOT / "RESEARCH_RESULTS.csv"
# Full allocation ablation is evaluated at these representative budgets on the
# large dictionary. Synthetic controls cover the complete 2..20 range.
DICTIONARY_K_VALUES = (2, 3, 4, 5, 6, 8, 10, 12, 16, 20)
SYNTHETIC_K_VALUES = tuple(range(2, 21))
SYNTHETIC_COUNT = 50_000


def load_words(path: Path = DICTIONARY) -> list[str]:
    with path.open("r", encoding="utf-8") as handle:
        return [line.strip().lower() for line in handle if line.strip()]


def add_selector_rows(rows: list[dict], dataset: str, words: list[str], k: int) -> None:
    representations = strategy_representations(words, k)
    for strategy, values in representations.items():
        stats = collision_stats(values)
        groups = collision_group_distribution(values)
        rows.append({
            "experiment": "selector",
            "dataset": dataset,
            "k": k,
            "strategy": strategy,
            "front": k // 2 if strategy == "HPSS" else "",
            "back": k - k // 2 if strategy == "HPSS" else "",
            "records": len(words),
            "unique": stats["unique"],
            "collision_entries": stats["collision_entries"],
            "collision_rate": stats["collision_rate"],
            "collision_pairs": stats["collision_pairs"],
            "max_group": stats["max_group"],
            "collision_groups": sum(groups.values()),
            "notes": "balanced HPSS allocation" if strategy == "HPSS" else "",
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
            "collision_rate": result.collision_entries / len(words) if words else 0.0,
            "collision_pairs": result.collision_pairs,
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
            stats = collision_stats(values)
            rows.append({
                "experiment": "length",
                "dataset": dataset,
                "k": k,
                "strategy": strategy,
                "front": "",
                "back": "",
                "records": len(bucket_words),
                "unique": stats["unique"],
                "collision_entries": stats["collision_entries"],
                "collision_rate": stats["collision_rate"],
                "collision_pairs": stats["collision_pairs"],
                "max_group": stats["max_group"],
                "collision_groups": "",
                "notes": f"length_bucket={bucket}",
            })


def main() -> None:
    datasets = {
        "english-word": (load_words(), DICTIONARY_K_VALUES),
        "random-alphanumeric": (generate_random_strings(SYNTHETIC_COUNT), SYNTHETIC_K_VALUES),
        "structured-identifier": (generate_structured_identifiers(SYNTHETIC_COUNT), SYNTHETIC_K_VALUES),
    }
    rows: list[dict] = []

    for dataset, (words, k_values) in datasets.items():
        for k in k_values:
            add_allocation_rows(rows, dataset, words, k)
            add_selector_rows(rows, dataset, words, k)

        if dataset == "english-word":
            for k in (4, 8, 12, 16, 20):
                add_length_rows(rows, dataset, words, k)

    fieldnames = [
        "experiment", "dataset", "k", "strategy", "front", "back", "records",
        "unique", "collision_entries", "collision_rate", "collision_pairs",
        "max_group", "collision_groups", "notes",
    ]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {OUTPUT} with {len(rows):,} rows")
    print("Datasets:", ", ".join(datasets))
    print("Synthetic controls:", SYNTHETIC_COUNT, "records each")


if __name__ == "__main__":
    main()
