import pytest

from hpss_hash import (
    CompiledEncoder,
    HPSSHasher,
    hpss_positional_hash,
    select_hpss,
    select_middle,
    select_prefix,
    select_suffix,
)


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
