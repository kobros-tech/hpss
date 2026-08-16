import pytest

from research_experiments import (
    allocation_ablation,
    bootstrap_mean_difference,
    collision_group_distribution,
    generate_random_strings,
    generate_structured_identifiers,
    hpss_matches_balanced_allocation,
    length_buckets,
    select_allocation,
)


def test_allocation_matches_hpss_for_even_k():
    words = ["abcdefghij", "encyclopedia", "algorithm"]
    assert hpss_matches_balanced_allocation(words, 6)
    assert select_allocation("abcdefghij", 6, 3) == "abcfghij"


def test_allocation_matches_hpss_for_odd_k():
    words = ["abcdefghij", "encyclopedia", "algorithm"]
    assert hpss_matches_balanced_allocation(words, 5)
    assert select_allocation("abcdefghij", 5, 2) == "abhij"


def test_allocation_rejects_invalid_front_count():
    with pytest.raises(ValueError):
        select_allocation("abcdefgh", 5, -1)
    with pytest.raises(ValueError):
        select_allocation("abcdefgh", 5, 6)


def test_allocation_ablation_exhausts_every_split():
    results = allocation_ablation(["abcdefghij", "abcdefghi"], 5)
    assert [(r.front, r.back) for r in results] == [(0, 5), (1, 4), (2, 3), (3, 2), (4, 1), (5, 0)]
    assert results[2].unique == len(set(["abhij", "abghi"]))


def test_collision_group_distribution():
    assert collision_group_distribution(["a", "a", "b", "b", "b", "c"]) == {2: 1, 3: 1}


def test_length_buckets_are_disjoint_and_complete():
    words = ["a", "abcd", "abcdefgh", "abcdefghijkl", "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz"]
    buckets = length_buckets(words)
    flattened = [word for values in buckets.values() for word in values]
    assert sorted(flattened) == sorted(words)


def test_synthetic_controls_are_deterministic():
    assert generate_random_strings(10, 8) == generate_random_strings(10, 8)
    assert generate_structured_identifiers(10) == generate_structured_identifiers(10)
    assert len(set(generate_random_strings(100, 8))) == 100


def test_bootstrap_mean_difference_is_paired():
    mean, low, high = bootstrap_mean_difference([1, 2, 3], [2, 4, 6], iterations=1000)
    assert mean == pytest.approx(2.0)
    assert low <= mean <= high
