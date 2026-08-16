"""Exhaustive HPSS front/back allocation ablation on the real dictionary.

For each k and every split p + (k-p), this benchmark measures the
representation produced by taking p characters from the front and k-p from
the back. The goal is to test whether the balanced HPSS allocation is actually
optimal rather than assuming that it is.
"""

from __future__ import annotations

import csv
from pathlib import Path

from benchmark import K_VALUES, collision_stats, load_words
from research_experiments import allocation_ablation

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "ALLOCATION_ABLATION.csv"


def main() -> None:
    words = load_words()
    rows: list[dict[str, int | float | str]] = []

    for k in K_VALUES:
        results = allocation_ablation(words, k)
        best_unique = max(result.unique for result in results)
        best_pair = min(result.collision_pairs for result in results)
        balanced_front = k // 2

        for result in results:
            rows.append({
                "dataset": "dwyl/english-word",
                "k": result.k,
                "front": result.front,
                "back": result.back,
                "allocation": f"{result.front}+{result.back}",
                "records": result.records,
                "unique": result.unique,
                "unique_rate": result.unique_rate,
                "collision_entries": result.collision_entries,
                "collision_pairs": result.collision_pairs,
                "max_group": result.max_group,
                "is_balanced_hpss": int(result.front == balanced_front),
                "is_best_unique": int(result.unique == best_unique),
                "is_best_collision_pairs": int(result.collision_pairs == best_pair),
            })

        winners = [
            f"{r.front}+{r.back}"
            for r in results
            if r.unique == best_unique
        ]
        balanced = results[balanced_front]
        print(
            f"k={k}: best_unique={best_unique:,} ({', '.join(winners)}); "
            f"balanced={balanced.front}+{balanced.back} -> {balanced.unique:,}"
        )

    fieldnames = list(rows[0])
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Loaded {len(words):,} records")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
