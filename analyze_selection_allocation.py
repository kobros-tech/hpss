"""Analyze exhaustive prefix/suffix allocation results.

For a fixed character budget k, only k+1 prefix/suffix allocations exist.
This module summarizes those allocations by exact collision objectives and by
measured speed. Runtime uncertainty is retained from the bootstrap confidence
intervals produced by ``research_ratio_experiment.py``.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def alpha_interval(front: int, k: int) -> tuple[float, float]:
    """Return the alpha interval producing a given integer allocation."""
    if k <= 0 or not 0 <= front <= k:
        raise ValueError("front must be between 0 and k, with k positive")
    low = max(0.0, (front - 0.5) / k)
    high = min(1.0, (front + 0.5) / k)
    return low, high


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def summary_row(k: int, objective: str, row: dict[str, str]) -> dict[str, object]:
    front = int(row["front"])
    low, high = alpha_interval(front, k)
    result: dict[str, object] = {
        "k": k,
        "objective": objective,
        "front": front,
        "suffix": int(row["suffix"]),
        "alpha": float(row["alpha"]),
        "alpha_interval_low": low,
        "alpha_interval_high": high,
        "unique": int(row["unique"]),
        "collision_entries": int(row["collision_entries"]),
        "collision_rate": float(row["collision_rate"]),
        "collision_pairs": int(row["collision_pairs"]),
        "max_group": int(row["max_group"]),
        "median_seconds": float(row["median_seconds"]),
        "throughput_words_per_second": float(row["throughput_words_per_second"]),
    }
    for field in (
        "timing_iqr_seconds",
        "timing_ci95_low",
        "timing_ci95_high",
        "throughput_ci95_low",
        "throughput_ci95_high",
    ):
        if field in row:
            result[field] = float(row[field])
    if "timing_repeats" in row:
        result["timing_repeats"] = int(row["timing_repeats"])
    return result


def summarize(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    groups: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[int(row["k"])].append(row)

    output: list[dict[str, object]] = []
    objectives = (
        ("collision_entries", "min"),
        ("collision_pairs", "min"),
        ("max_group", "min"),
        ("throughput_words_per_second", "max"),
    )

    for k, allocation_rows in sorted(groups.items()):
        for objective, direction in objectives:
            key = lambda row: float(row[objective])
            best = min(allocation_rows, key=key) if direction == "min" else max(allocation_rows, key=key)
            output.append(summary_row(k, objective, best))

        # Pareto frontier: maximize uniqueness and throughput while minimizing
        # collision pairs. An allocation is dominated if another is at least
        # as good on all three objectives and strictly better on one.
        def dominates(a: dict[str, str], b: dict[str, str]) -> bool:
            a_values = (
                int(a["unique"]),
                -int(a["collision_pairs"]),
                float(a["throughput_words_per_second"]),
            )
            b_values = (
                int(b["unique"]),
                -int(b["collision_pairs"]),
                float(b["throughput_words_per_second"]),
            )
            return all(x >= y for x, y in zip(a_values, b_values)) and any(
                x > y for x, y in zip(a_values, b_values)
            )

        frontier = [
            row
            for row in allocation_rows
            if not any(
                dominates(other, row)
                for other in allocation_rows
                if other is not row
            )
        ]
        for row in sorted(frontier, key=lambda item: int(item["front"])):
            output.append(
                summary_row(k, "pareto_unique_collision_pairs_throughput", row)
            )

    return output


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    if not rows:
        raise ValueError("no rows to write")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = read_rows(args.input)
    write_csv(summarize(rows), args.output)


if __name__ == "__main__":
    main()
