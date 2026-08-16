"""Run exhaustive front/back allocation experiments across ASCII datasets."""

from __future__ import annotations

import csv
from pathlib import Path

from benchmark import K_VALUES
from research_experiments import allocation_ablation, generate_random_strings

ROOT = Path(__file__).resolve().parent
DATASET_PATHS = {
    "dwyl/english-word": ROOT / "dictionaries/words.txt",
    "Estonian domains": ROOT / "dictionaries/estonian_domains.txt",
}
RANDOM_COUNT = 50_000
RANDOM_LENGTH = 16
RANDOM_SEED = 20260816
OUTPUT = ROOT / "MULTI_DATASET_ALLOCATION_ABLATION.csv"


def load(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def run_dataset(dataset: str, values: list[str], rows: list[dict]) -> None:
    if not values:
        raise ValueError(f"{dataset} is empty")
    if not all(all(ord(c) < 128 for c in value) for value in values):
        raise ValueError(f"{dataset} contains non-ASCII input")
    print(f"\n=== {dataset} ({len(values):,} records) ===")
    for k in K_VALUES:
        results = allocation_ablation(values, k)
        best_unique = max(r.unique for r in results)
        balanced_front = k // 2
        balanced = results[balanced_front]
        winners = [f"{r.front}+{r.back}" for r in results if r.unique == best_unique]
        print(
            f"k={k:2d}: best={','.join(winners):>6s} "
            f"{best_unique:>8,}; balanced={balanced.front}+{balanced.back} "
            f"{balanced.unique:>8,}"
        )
        for r in results:
            rows.append({
                "dataset": dataset,
                "k": r.k,
                "front": r.front,
                "back": r.back,
                "allocation": f"{r.front}+{r.back}",
                "records": r.records,
                "unique": r.unique,
                "unique_rate": r.unique_rate,
                "collision_entries": r.collision_entries,
                "collision_pairs": r.collision_pairs,
                "max_group": r.max_group,
                "is_balanced_hpss": int(r.front == balanced_front),
                "is_best_unique": int(r.unique == best_unique),
            })


def main() -> None:
    rows: list[dict] = []
    for dataset, path in DATASET_PATHS.items():
        run_dataset(dataset, load(path), rows)

    random_values = generate_random_strings(
        count=RANDOM_COUNT,
        length=RANDOM_LENGTH,
        seed=RANDOM_SEED,
    )
    run_dataset(
        f"random ASCII ({RANDOM_LENGTH}-char, seed={RANDOM_SEED})",
        random_values,
        rows,
    )

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main()
