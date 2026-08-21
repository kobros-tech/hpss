from research_selection_experiment import (
    benchmark_pipeline,
    ratio_prefix_count,
    run,
    select_representation,
)


def test_ratio_extremes_match_prefix_and_suffix():
    word = "abcdefgh"
    assert select_representation(word, 4, 0.0) == "efgh"
    assert select_representation(word, 4, 1.0) == "abcd"


def test_ratio_half_is_balanced_for_even_k():
    assert select_representation("abcdefgh", 6, 0.5) == "abcfgh"
    assert ratio_prefix_count(6, 0.5) == 3


def test_ratio_uses_round_half_up_for_odd_k():
    assert ratio_prefix_count(5, 0.5) == 3
    assert select_representation("abcdefgh", 5, 0.5) == "abcgh"


def test_no_selection_returns_word_unchanged():
    word = "Example"
    assert select_representation(word, 8, None) == word


def test_benchmark_records_baseline_and_ratio_rows():
    words = ["abcdef", "abcdeg", "xyzabc"]
    rows = run(words, [4], [0.0, 0.5, 1.0], repeats=1)

    assert len(rows) == 4
    assert rows[0]["selection"] == "NONE"
    assert rows[1]["selection"] == "HPSS_RATIO"
    assert rows[1]["alpha"] == 0.0
    assert rows[-1]["alpha"] == 1.0
    assert all(row["hash"] == "XXHASH64" for row in rows)


def test_benchmark_accepts_empty_input():
    row = benchmark_pipeline([], 4, 0.5, repeats=1)
    assert row["words"] == 0
    assert row["representation_unique"] == 0
    assert row["hash_unique"] == 0
