"""
======================================================================
REAL-WORLD HPSS BENCHMARK
======================================================================

Benchmark HPSS against established 64-bit hash functions on a
real-world dictionary containing letters, numbers, punctuation,
apostrophes, and other supported characters.

Current dataset:

    dictionaries/words.txt

The benchmark measures two different sources of collisions:

1. REPRESENTATION COLLISIONS
   --------------------------------
   Caused by the character-selection strategy itself.

   Example:

       word A -> "abcd....wxyz"
       word B -> "abcd....wxyz"

   If both words produce the same selected representation, they are
   already indistinguishable before any hash function is applied.

   These collisions belong to the SELECTION STRATEGY.

2. HASH COLLISIONS
   --------------------------------
   Collisions among distinct representations after applying the hash
   function.

   For HPSS_POSITIONAL, distinct representations should remain
   distinct because the Unicode positional encoder is injective.

   For FNV-1a, MurmurHash3, and xxHash64, collisions are theoretically
   possible because they produce fixed-width 64-bit outputs.

The benchmark deliberately applies the reference hash functions to
the SAME selected representations produced by each strategy.

This allows us to separate:

    selection quality
            from
    hash-function behavior

======================================================================
RUN
======================================================================

    python3.11 benchmark.py

Produces:

    RESULTS_fresh.csv

======================================================================
"""

from __future__ import annotations

import csv
import statistics
import time
from collections import Counter

from hpss_hash import (
    REFERENCE_HASHES,
    SELECTION_STRATEGIES,
    CompiledEncoder,
)


# ======================================================================
# CONFIGURATION
# ======================================================================

# Real-world dictionary containing letters, numbers, punctuation,
# apostrophes, and potentially other characters.
DICTIONARY = "dictionaries/words.txt"

# Number of selected characters.
K_VALUES = [2, 4, 6, 8, 10, 12]

# Number of timing repetitions.
REPETITIONS = 5


# ======================================================================
# HPSS POSITIONAL ENCODER
# ======================================================================

# No explicit alphabet is supplied.
#
# Therefore CompiledEncoder() uses the Unicode code-point encoder:
#
#     digit(c) = ord(c) + 1
#
# This supports:
#
#     a-z
#     A-Z
#     0-9
#     punctuation
#     symbols
#     Unicode characters
#
# without silently discarding anything.

hpss_encode = CompiledEncoder()


# ======================================================================
# DATASET
# ======================================================================

def load_words(path: str = DICTIONARY) -> list[str]:
    """
    Load one key/word per line.

    Empty lines are ignored.

    Keys are converted to lowercase so the benchmark treats uppercase
    and lowercase versions of the same textual key as equivalent.
    """

    with open(path, "r", encoding="utf-8") as f:
        return [
            line.strip().lower()
            for line in f
            if line.strip()
        ]


# ======================================================================
# COLLISION STATISTICS
# ======================================================================

def collision_stats(values) -> dict:
    """
    Calculate detailed collision statistics.

    Returns:

        unique
            Number of unique values.

        collision_entries
            Number of input entries that are not represented uniquely.

            n - unique

        collision_entry_rate
            collision_entries / n

        collision_pairs
            Number of colliding pairs.

            For a group of frequency f:

                f * (f - 1) / 2

        max_group
            Size of the largest collision group.
    """

    n = len(values)

    if n == 0:
        return {
            "unique": 0,
            "collision_entries": 0,
            "collision_entry_rate": 0.0,
            "collision_pairs": 0,
            "max_group": 0,
        }

    counts = Counter(values)

    unique = len(counts)

    collision_entries = n - unique

    collision_entry_rate = collision_entries / n

    collision_pairs = sum(
        f * (f - 1) // 2
        for f in counts.values()
        if f >= 2
    )

    max_group = max(counts.values())

    return {
        "unique": unique,
        "collision_entries": collision_entries,
        "collision_entry_rate": collision_entry_rate,
        "collision_pairs": collision_pairs,
        "max_group": max_group,
    }


# ======================================================================
# TIMING
# ======================================================================

def timeit(
    fn,
    items,
    repetitions: int = REPETITIONS,
):
    """
    Benchmark a function over all items.

    Returns:

        median_seconds
        items_per_second

    Median timing is used to reduce the influence of occasional
    operating-system scheduling noise.
    """

    timings = []

    for _ in range(repetitions):

        start = time.perf_counter()

        for item in items:
            fn(item)

        elapsed = time.perf_counter() - start

        timings.append(elapsed)

    median = statistics.median(timings)

    throughput = len(items) / median

    return median, throughput


# ======================================================================
# MAIN BENCHMARK
# ======================================================================

def main():

    # --------------------------------------------------------------
    # LOAD DATASET
    # --------------------------------------------------------------

    words = load_words()

    n = len(words)

    print(
        f"Loaded {n:,} words from {DICTIONARY}"
    )

    # --------------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------------

    rows = []

    # --------------------------------------------------------------
    # K VALUES
    # --------------------------------------------------------------

    for k in K_VALUES:

        # ----------------------------------------------------------
        # SELECTION STRATEGIES
        # ----------------------------------------------------------

        for strat_name, selector in SELECTION_STRATEGIES.items():

            # ------------------------------------------------------
            # CREATE REPRESENTATIONS
            # ------------------------------------------------------

            reps = [
                selector(word, k)
                for word in words
            ]

            # ------------------------------------------------------
            # UTF-8 REPRESENTATIONS FOR REFERENCE HASHES
            # ------------------------------------------------------

            # IMPORTANT:
            #
            # The old benchmark used:
            #
            #     encode("ascii", errors="ignore")
            #
            # which silently discarded unsupported characters.
            #
            # That would make the experiment invalid for a dataset
            # containing Unicode characters.
            #
            # UTF-8 preserves the complete selected representation.

            rep_bytes = [
                representation.encode("utf-8")
                for representation in reps
            ]

            # ------------------------------------------------------
            # REPRESENTATION COLLISION STATISTICS
            # ------------------------------------------------------

            rep_stats = collision_stats(reps)

            # ------------------------------------------------------
            # HPSS POSITIONAL ENCODER
            # ------------------------------------------------------

            hpss_vals = [
                hpss_encode(representation)
                for representation in reps
            ]

            hpss_stats = collision_stats(
                hpss_vals
            )

            _, hpss_speed = timeit(
                hpss_encode,
                reps,
            )

            # ------------------------------------------------------
            # HPSS RESULT
            # ------------------------------------------------------

            rows.append({
                "k": k,
                "strategy": strat_name,
                "words": n,

                "representation_unique":
                    rep_stats["unique"],

                "representation_collision_entries":
                    rep_stats["collision_entries"],

                "representation_collision_rate":
                    rep_stats["collision_entry_rate"],

                "representation_collision_pairs":
                    rep_stats["collision_pairs"],

                "representation_max_group":
                    rep_stats["max_group"],

                "hash":
                    "HPSS_POSITIONAL",

                "hash_unique":
                    hpss_stats["unique"],

                "hash_collision_entries":
                    hpss_stats["collision_entries"],

                "hash_collision_rate":
                    hpss_stats["collision_entry_rate"],

                "hash_collision_pairs":
                    hpss_stats["collision_pairs"],

                "hash_max_group":
                    hpss_stats["max_group"],

                "hashes_per_second":
                    hpss_speed,
            })

            # ------------------------------------------------------
            # REFERENCE HASH FUNCTIONS
            # ------------------------------------------------------

            for hash_name, hash_fn in REFERENCE_HASHES.items():

                try:

                    vals = [
                        hash_fn(data)
                        for data in rep_bytes
                    ]

                except RuntimeError as exc:

                    print(
                        f"skipping {hash_name}: {exc}"
                    )

                    continue

                stats = collision_stats(vals)

                _, speed = timeit(
                    hash_fn,
                    rep_bytes,
                )

                rows.append({
                    "k": k,
                    "strategy": strat_name,
                    "words": n,

                    "representation_unique":
                        rep_stats["unique"],

                    "representation_collision_entries":
                        rep_stats["collision_entries"],

                    "representation_collision_rate":
                        rep_stats["collision_entry_rate"],

                    "representation_collision_pairs":
                        rep_stats["collision_pairs"],

                    "representation_max_group":
                        rep_stats["max_group"],

                    "hash":
                        hash_name,

                    "hash_unique":
                        stats["unique"],

                    "hash_collision_entries":
                        stats["collision_entries"],

                    "hash_collision_rate":
                        stats["collision_entry_rate"],

                    "hash_collision_pairs":
                        stats["collision_pairs"],

                    "hash_max_group":
                        stats["max_group"],

                    "hashes_per_second":
                        speed,
                })

        print(
            f"k={k} done"
        )

    # ==================================================================
    # WRITE CSV
    # ==================================================================

    output_file = "RESULTS_fresh.csv"

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()

        writer.writerows(rows)

    print(
        f"\nWrote {output_file}"
    )

    # ==================================================================
    # COMPACT HPSS SUMMARY
    # ==================================================================

    print(
        "\n"
        " k | hash             | unique  | coll.entries | "
        "coll.rate | coll.pairs | max.group | hashes/sec"
    )

    print("-" * 115)

    for row in rows:

        if row["strategy"] != "HPSS":
            continue

        print(
            f"{row['k']:2d} | "
            f"{row['hash']:<16} | "
            f"{row['hash_unique']:7,} | "
            f"{row['hash_collision_entries']:12,} | "
            f"{row['hash_collision_rate'] * 100:8.4f}% | "
            f"{row['hash_collision_pairs']:10,} | "
            f"{row['hash_max_group']:9,} | "
            f"{row['hashes_per_second']:11,.0f}"
        )


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    main()
