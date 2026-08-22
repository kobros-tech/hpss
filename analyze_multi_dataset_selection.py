"""Analyze front/back selection allocations across all research datasets.

The allocation itself is the experimental unit. ``alpha = front / k`` is
reported as a convenient ratio representation; the analysis never treats
alpha as a continuous variable because only k + 1 discrete allocations exist
for a fixed k.
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def alpha_interval(front: int, k: int) -> tuple[float, float]:
    """Return the half-up rounding interval for an allocation.

    The interval is ``[low, high)`` except that the final allocation is closed
    at 1.0. At an exact half-way point, half-up rounding assigns the value to
    the larger allocation.
    """
    if k <= 0 or not 0 <= front <= k:
        raise ValueError("invalid allocation")
    low = max(0.0, (front - 0.5) / k)
    high = min(1.0, (front + 0.5) / k)
    return low, high


def choose(group: list[dict[str, str]], metric: str, maximize: bool) -> list[dict[str, str]]:
    values = [int(row[metric]) for row in group]
    target = max(values) if maximize else min(values)
    return [row for row in group if int(row[metric]) == target]


def enrich(row: dict[str, str]) -> dict[str, str]:
    result = dict(row)
    k = int(row["k"])
    front = int(row["front"])
    lo, hi = alpha_interval(front, k)
    result["alpha"] = f"{front / k:.12g}"
    result["alpha_interval_low"] = f"{lo:.12g}"
    result["alpha_interval_high"] = f"{hi:.12g}"
    return result


def analyze(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    groups: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["dataset"], int(row["k"]))].append(row)

    outputs: dict[str, list[dict[str, str]]] = {
        "unique_optima": [],
        "collision_entries_optima": [],
        "collision_pairs_optima": [],
        "max_group_optima": [],
        "balanced_comparison": [],
    }

    for (dataset, k), group in sorted(groups.items()):
        for name, metric, maximize in (
            ("unique_optima", "unique", True),
            ("collision_entries_optima", "collision_entries", False),
            ("collision_pairs_optima", "collision_pairs", False),
            ("max_group_optima", "max_group", False),
        ):
            for row in choose(group, metric, maximize):
                outputs[name].append(enrich(row))

        balanced_front = k // 2
        balanced = next(row for row in group if int(row["front"]) == balanced_front)
        best_rows = choose(group, "unique", True)
        best_unique = int(best_rows[0]["unique"])
        best_allocations = ";".join(
            f"{row['front']}+{row['back']}" for row in best_rows
        )
        comparison = enrich(balanced)
        comparison["best_unique_allocations"] = best_allocations
        comparison["best_unique_allocation_count"] = str(len(best_rows))
        comparison["best_unique"] = str(best_unique)
        comparison["unique_gap_from_best"] = best_unique - int(balanced["unique"])
        comparison["is_balanced_best_unique"] = str(int(balanced["unique"] == best_unique))
        outputs["balanced_comparison"].append(comparison)

    return outputs


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    outputs = analyze(read_rows(args.input))
    for name, rows in outputs.items():
        write_csv(args.output_dir / f"selection_{name}.csv", rows)

    print("--- best allocation by unique representations ---")
    for row in outputs["unique_optima"]:
        print(
            f"dataset={row['dataset']} k={row['k']} "
            f"allocation={row['front']}+{row['back']} alpha={row['alpha']} "
            f"unique={row['unique']} collision_pairs={row['collision_pairs']}"
        )
    print(f"datasets={len({row['dataset'] for row in outputs['unique_optima']})}")


if __name__ == "__main__":
    main()
