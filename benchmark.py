"""
Real-world benchmark: HPSS vs. established hash functions, on the
CS50 "large" dictionary (143,091 English words/word-forms).

Produces RESULTS_fresh.csv and prints a summary table.

Two things are measured separately, on purpose:

  1. REPRESENTATION collisions -- caused by the selection strategy
     throwing away characters (e.g. two words sharing the same first
     4 + last 4 letters). Every hash function inherits these; they
     are a property of the *selection strategy*, not the hash.

  2. HASH collisions -- collisions among distinct representations.
     For the fixed HPSS encoder this should be exactly 0 (see
     test_no_collisions.py). For FNV-1a/MurmurHash3/xxHash this is
     governed by the birthday bound on a 64-bit output and is
     expected to be 0 at this dataset size too (143,091 << 2^32).

Run:
    python3 benchmark.py
"""

import csv
import statistics
import time
from collections import Counter

from hpss_hash import (
    ALPHABET_CS50,
    REFERENCE_HASHES,
    SELECTION_STRATEGIES,
    CompiledEncoder,
)

hpss_encode = CompiledEncoder(ALPHABET_CS50)

DICTIONARY = "dictionaries/large"
K_VALUES = [2, 4, 6, 8, 10, 12]
REPETITIONS = 5


def load_words(path: str = DICTIONARY) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


def collision_stats(values) -> dict:
    n = len(values)
    counts = Counter(values)
    unique = len(counts)
    entries = n - unique
    pairs = sum(f * (f - 1) // 2 for f in counts.values() if f >= 2)
    return {
        "unique": unique,
        "collision_entries": entries,
        "collision_entry_rate": entries / n,
        "collision_pairs": pairs,
        "max_group": max(counts.values()),
    }


def timeit(fn, items, repetitions=REPETITIONS):
    timings = []
    for _ in range(repetitions):
        start = time.perf_counter()
        for item in items:
            fn(item)
        timings.append(time.perf_counter() - start)
    median = statistics.median(timings)
    return median, len(items) / median


def main():
    words = load_words()
    n = len(words)
    print(f"Loaded {n:,} words from {DICTIONARY}")

    rows = []

    for k in K_VALUES:
        for strat_name, selector in SELECTION_STRATEGIES.items():
            reps = [selector(w, k) for w in words]
            rep_bytes = [r.encode("ascii", errors="ignore") for r in reps]

            rep_stats = collision_stats(reps)

            # --- HPSS positional encoder (own hash), using a
            # pre-compiled lookup table so the benchmark is fair
            # against the reference hashes below (which also do no
            # per-call setup work). ---
            hpss_vals = [hpss_encode(r) for r in reps]
            hpss_stats = collision_stats(hpss_vals)
            _, hpss_speed = timeit(hpss_encode, reps)

            row = {
                "k": k,
                "strategy": strat_name,
                "words": n,
                "representation_unique": rep_stats["unique"],
                "representation_collision_rate": rep_stats["collision_entry_rate"],
                "hash": "HPSS_POSITIONAL",
                "hash_unique": hpss_stats["unique"],
                "hash_collision_entries": hpss_stats["collision_entries"],
                "hash_collision_rate": hpss_stats["collision_entry_rate"],
                "hashes_per_second": hpss_speed,
            }
            rows.append(row)

            # --- reference hash functions, same representations ---
            for hash_name, hash_fn in REFERENCE_HASHES.items():
                try:
                    vals = [hash_fn(b) for b in rep_bytes]
                except RuntimeError as exc:
                    print(f"skipping {hash_name}: {exc}")
                    continue
                stats = collision_stats(vals)
                _, speed = timeit(hash_fn, rep_bytes)
                rows.append({
                    "k": k,
                    "strategy": strat_name,
                    "words": n,
                    "representation_unique": rep_stats["unique"],
                    "representation_collision_rate": rep_stats["collision_entry_rate"],
                    "hash": hash_name,
                    "hash_unique": stats["unique"],
                    "hash_collision_entries": stats["collision_entries"],
                    "hash_collision_rate": stats["collision_entry_rate"],
                    "hashes_per_second": speed,
                })

        print(f"k={k} done")

    with open("RESULTS_fresh.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("\nWrote RESULTS_fresh.csv")

    # ---- print a compact summary for HPSS selection only ----
    print("\n k | hash             | unique  | coll.entries | coll.rate | hashes/sec")
    print("-" * 80)
    for r in rows:
        if r["strategy"] != "HPSS":
            continue
        print(
            f"{r['k']:2d} | {r['hash']:<16} | {r['hash_unique']:7,} | "
            f"{r['hash_collision_entries']:12,} | "
            f"{r['hash_collision_rate']*100:8.4f}% | "
            f"{r['hashes_per_second']:11,.0f}"
        )


if __name__ == "__main__":
    main()
