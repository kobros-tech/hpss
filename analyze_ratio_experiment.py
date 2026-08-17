"""Summarize ratio-allocation experiment results.

Produces separate optima for each collision metric, the speed optimum, and a
Pareto frontier based on collision pairs versus throughput.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def pareto_frontier(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Minimize collision pairs and maximize throughput."""
    frontier = []
    for candidate in rows:
        cp = int(candidate["collision_pairs"])
        speed = float(candidate["throughput_words_per_second"])
        dominated = any(
            int(other["collision_pairs"]) <= cp
            and float(other["throughput_words_per_second"]) >= speed
            and (
                int(other["collision_pairs"]) < cp
                or float(other["throughput_words_per_second"]) > speed
            )
            for other in rows
        )
        if not dominated:
            frontier.append(candidate)
    return sorted(
        frontier,
        key=lambda row: (
            int(row["k"]),
            int(row["collision_pairs"]),
            -float(row["throughput_words_per_second"]),
        ),
    )


def choose_optima(group: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {
        "unique": max(group, key=lambda row: (int(row["unique"]), -int(row["collision_pairs"]))),
        "collision_entries": min(group, key=lambda row: (int(row["collision_entries"]), int(row["collision_pairs"]))),
        "collision_pairs": min(group, key=lambda row: (int(row["collision_pairs"]), int(row["collision_entries"]))),
        "max_group": min(group, key=lambda row: (int(row["max_group"]), int(row["collision_pairs"]))),
        "speed": max(group, key=lambda row: (float(row["throughput_words_per_second"]), -int(row["collision_pairs"]))),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    rows = read_rows(args.input)
    by_k: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        by_k.setdefault(int(row["k"]), []).append(row)

    outputs = {
        "unique": [],
        "collision_entries": [],
        "collision_pairs": [],
        "max_group": [],
        "speed": [],
    }
    pareto = []

    for k, group in sorted(by_k.items()):
        optima = choose_optima(group)
        for metric, row in optima.items():
            outputs[metric].append(row)
        pareto.extend(pareto_frontier(group))

    for metric, rows_out in outputs.items():
        write_rows(args.output_dir / f"ratio_{metric}_optima.csv", rows_out)
    write_rows(args.output_dir / "ratio_pareto_frontier.csv", pareto)

    print("--- optima by metric ---")
    for metric, rows_out in outputs.items():
        print(f"[{metric}]")
        for row in rows_out:
            print(
                f"k={row['k']} front={row['front']} suffix={row['suffix']} "
                f"alpha={row['alpha']} unique={row['unique']} "
                f"entries={row['collision_entries']} pairs={row['collision_pairs']} "
                f"max_group={row['max_group']} speed={row['throughput_words_per_second']}"
            )
    print(f"Pareto configurations: {len(pareto)}")


if __name__ == "__main__":
    main()
