"""Summarize ratio-allocation experiment results.

Produces collision-optimal, speed-optimal, and Pareto-frontier CSV files.
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
    # Minimize collision pairs and maximize throughput.
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
    return sorted(frontier, key=lambda row: (int(row["k"]), int(row["collision_pairs"]), -float(row["throughput_words_per_second"])))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    rows = read_rows(args.input)
    by_k: dict[int, list[dict[str, str]]] = {}
    for row in rows:
        by_k.setdefault(int(row["k"]), []).append(row)

    collision_optima = []
    speed_optima = []
    pareto = []

    for k, group in sorted(by_k.items()):
        best_collision = min(group, key=lambda row: (int(row["collision_pairs"]), int(row["collision_entries"]), -int(row["unique"])))
        best_speed = max(group, key=lambda row: (float(row["throughput_words_per_second"]), -int(row["collision_pairs"])))
        collision_optima.append(best_collision)
        speed_optima.append(best_speed)
        pareto.extend(pareto_frontier(group))

    write_rows(args.output_dir / "ratio_collision_optima.csv", collision_optima)
    write_rows(args.output_dir / "ratio_speed_optima.csv", speed_optima)
    write_rows(args.output_dir / "ratio_pareto_frontier.csv", pareto)

    print("--- collision optima ---")
    for row in collision_optima:
        print(f"k={row['k']} alpha={row['alpha']} pairs={row['collision_pairs']} unique={row['unique']}")
    print("--- speed optima ---")
    for row in speed_optima:
        print(f"k={row['k']} alpha={row['alpha']} throughput={row['throughput_words_per_second']}")
    print(f"Pareto configurations: {len(pareto)}")


if __name__ == "__main__":
    main()
