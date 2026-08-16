import pytest

from benchmark import collision_stats
from hpss_hash import (
    CompiledEncoder,
    HPSSHasher,
    hpss_positional_hash,
    select_hpss,
    select_middle,
    select_prefix,
    select_suffix,
)

ALL_SELECTORS = (select_prefix, select_suffix, select_hpss, select_middle)


def test_odd_k_hpss_rule():
    assert select_hpss("abcdefghij", 5) == "ab" + "hij"
    assert len(select_hpss("abcdefghij", 5)) == 5


def test_even_k_hpss_rule():
    assert select_hpss("abcdefghij", 6) == "abc" + "hij"


def test_short_words_are_not_truncated():
    for selector in (select_prefix, select_suffix, select_hpss, select_middle):
        assert selector("abc", 5) == "abc"


def test_hpss_has_exact_length_when_long_enough():
    for k in range(0, 13):
        result = select_hpss("abcdefghijklmnopqrstuvwxyz", k)
        assert len(result) == k


def test_unicode_encoder_is_injective_on_small_exhaustive_set():
    strings = ["", "a", "b", "aa", "ab", "ba", "é", "中", "aé", "éa"]
    values = [hpss_positional_hash(s) for s in strings]
    assert len(values) == len(set(values))


def test_compiled_encoder_matches_function():
    encoder = CompiledEncoder()
    for text in ["", "abc", "don't", "é中", "100%"]:
        assert encoder(text) == hpss_positional_hash(text)


def test_closed_alphabet_unknown_character_raises():
    with pytest.raises(ValueError):
        hpss_positional_hash("abc!", "abc")


def test_table_index_requires_positive_size():
    with pytest.raises(ValueError):
        HPSSHasher(k=5).table_index("abcdef", 0)


@pytest.mark.parametrize("selector", ALL_SELECTORS)
def test_selectors_reject_negative_k(selector):
    with pytest.raises(ValueError):
        selector("abcdefgh", -1)


def test_hpss_k_zero_returns_empty_string():
    # Regression test for the historical bug: with the old
    # `word[:half] + word[-half:]` formulation, `half=0` made
    # `word[-0:]` evaluate to `word[0:]` (the whole word, since
    # `-0 == 0` in Python) instead of the empty string.
    assert select_hpss("abcdefghij", 0) == ""
    assert select_hpss("x", 0) == ""


def test_collision_stats_hand_computed_example():
    # ["a", "a", "b"] -> 2 unique values, 1 collision entry, 1 pair,
    # largest group has 2 members.
    stats = collision_stats(["a", "a", "b"])
    assert stats["unique"] == 2
    assert stats["collision_entries"] == 1
    assert stats["collision_entry_rate"] == pytest.approx(1 / 3)
    assert stats["collision_pairs"] == 1
    assert stats["max_group"] == 2


def test_collision_stats_no_collisions():
    stats = collision_stats(["a", "b", "c"])
    assert stats["unique"] == 3
    assert stats["collision_entries"] == 0
    assert stats["collision_pairs"] == 0
    assert stats["max_group"] == 1


def test_collision_stats_empty_input():
    stats = collision_stats([])
    assert stats == {
        "unique": 0,
        "collision_entries": 0,
        "collision_entry_rate": 0.0,
        "collision_pairs": 0,
        "max_group": 0,
    }
