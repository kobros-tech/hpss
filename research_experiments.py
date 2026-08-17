"""Research experiments for HPSS selection.

This module adds the experiments motivated by peer review:

* exhaustive front/back allocation ablation for a fixed character budget;
* deterministic random-string and structured-identifier controls;
* collision-group distribution summaries;
* bootstrap confidence intervals for paired uniqueness differences;
* input-length stratification.

The experiments deliberately keep *selection* separate from downstream
hashing. The primary outcome is therefore representation uniqueness; the
reference hash functions are optional secondary checks.
"""

from __future__ import annotations

import random
import statistics
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from hpss_hash import SELECTION_STRATEGIES, select_hpss


@dataclass(frozen=True)
class AllocationResult:
    """Result for one front/back allocation of a fixed budget."""

    k: int
    front: int
    back: int
    unique: int
    collision_entries: int
    collision_pairs: int
    max_group: int
    records: int

    @property
    def unique_rate(self) -> float:
        return self.unique / self.records if self.records else 0.0


def collision_stats(values: Iterable[str]) -> dict[str, int | float]:
    """Compute representation collision statistics without hashing."""
    values = list(values)
    n = len(values)
    if not n:
        return {
            "unique": 0,
            "collision_entries": 0,
            "collision_rate": 0.0,
            "collision_pairs": 0,
            "max_group": 0,
        }
    counts = Counter(values)
    unique = len(counts)
    return {
        "unique": unique,
        "collision_entries": n - unique,
        "collision_rate": (n - unique) / n,
        "collision_pairs": sum(v * (v - 1) // 2 for v in counts.values() if v > 1),
        "max_group": max(counts.values()),
    }


def select_allocation(word: str, k: int, front: int) -> str:
    """Select ``front`` characters from the front and the remainder from back."""
    if k < 0:
        raise ValueError("k must be non-negative")
    if not 0 <= front <= k:
        raise ValueError("front must satisfy 0 <= front <= k")
    if len(word) <= k:
        return word
    back = k - front
    left = word[:front] if front else ""
    right = word[-back:] if back else ""
    return left + right


def allocation_ablation(words: Iterable[str], k: int) -> list[AllocationResult]:
    """Evaluate every possible front/back allocation for a fixed k."""
    words = list(words)
    results: list[AllocationResult] = []
    for front in range(k + 1):
        back = k - front
        reps = [select_allocation(word, k, front) for word in words]
        stats = collision_stats(reps)
        results.append(
            AllocationResult(
                k=k,
                front=front,
                back=back,
                unique=int(stats["unique"]),
                collision_entries=int(stats["collision_entries"]),
                collision_pairs=int(stats["collision_pairs"]),
                max_group=int(stats["max_group"]),
                records=len(words),
            )
        )
    return results


def hpss_matches_balanced_allocation(words: Iterable[str], k: int) -> bool:
    """Verify that the current HPSS rule equals the balanced allocation."""
    front = k // 2
    return all(select_hpss(word, k) == select_allocation(word, k, front) for word in words)


def collision_group_distribution(values: Iterable[str]) -> dict[int, int]:
    """Return group_size -> number_of_groups for groups containing >1 item."""
    counts = Counter(values)
    return dict(sorted(Counter(v for v in counts.values() if v > 1).items()))


def length_buckets(words: Iterable[str], boundaries: tuple[int, ...] = (4, 8, 12, 20, 32)) -> dict[str, list[str]]:
    """Split strings into reproducible length buckets."""
    result: dict[str, list[str]] = {}
    previous = 0
    for boundary in boundaries:
        result[f"{previous + 1}-{boundary}"] = []
        previous = boundary
    result[f"{previous + 1}+"] = []
    for word in words:
        length = len(word)
        placed = False
        previous = 0
        for boundary in boundaries:
            if length <= boundary:
                result[f"{previous + 1}-{boundary}"].append(word)
                placed = True
                break
            previous = boundary
        if not placed:
            result[f"{boundaries[-1] + 1}+"] .append(word)
    return {key: value for key, value in result.items() if value}


def generate_random_strings(count: int = 50_000, length: int = 16, seed: int = 20260816) -> list[str]:
    """Generate deterministic random lowercase-alphanumeric controls."""
    rng = random.Random(seed)
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return ["".join(rng.choice(alphabet) for _ in range(length)) for _ in range(count)]


def generate_structured_identifiers(count: int = 50_000, seed: int = 20260816) -> list[str]:
    """Generate deterministic identifiers with structured prefix/suffix fields."""
    rng = random.Random(seed)
    return [
        f"svc-{rng.randrange(1000):03d}-region-{rng.choice(['eu', 'us', 'ap'])}-{rng.randrange(100000):05d}"
        for _ in range(count)
    ]


def bootstrap_mean_difference(
    baseline: Iterable[int], treatment: Iterable[int], *,
    iterations: int = 5000, seed: int = 20260816,
) -> tuple[float, float, float]:
    """Bootstrap mean(treatment-baseline) and return a 95% percentile CI."""
    if iterations < 100:
        raise ValueError("iterations must be at least 100")
    baseline = list(baseline)
    treatment = list(treatment)
    if len(baseline) != len(treatment) or not baseline:
        raise ValueError("paired samples must be non-empty and have equal length")
    differences = [t - b for b, t in zip(baseline, treatment)]
    rng = random.Random(seed)
    samples = [statistics.mean(rng.choices(differences, k=len(differences))) for _ in range(iterations)]
    samples.sort()
    low = samples[int(0.025 * (len(samples) - 1))]
    high = samples[int(0.975 * (len(samples) - 1))]
    return statistics.mean(differences), low, high


def strategy_representations(words: Iterable[str], k: int) -> dict[str, list[str]]:
    """Materialize all standard selector representations for one dataset."""
    words = list(words)
    return {name: [selector(word, k) for word in words] for name, selector in SELECTION_STRATEGIES.items()}
