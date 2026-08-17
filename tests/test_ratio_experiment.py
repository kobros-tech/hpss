from pathlib import Path

from research_ratio_experiment import alpha_for_allocation, collision_stats, load_words


def test_alpha_interval_for_allocation():
    assert alpha_for_allocation(6, 8) == (0.6875, 0.8125)
    assert alpha_for_allocation(0, 8) == (0.0, 0.0625)
    assert alpha_for_allocation(8, 8) == (0.9375, 1.0)


def test_collision_stats():
    unique, entries, pairs, maximum = collision_stats(["a", "a", "b", "c", "c", "c"])
    assert unique == 3
    assert entries == 2
    assert pairs == 4  # C(2,2) + C(3,2)
    assert maximum == 3


def test_load_words_deduplicates_and_normalizes(tmp_path: Path):
    path = tmp_path / "words.txt"
    path.write_text("Apple\n apple \nBANANA\n\n", encoding="utf-8")
    assert load_words(path) == ["apple", "banana"]
