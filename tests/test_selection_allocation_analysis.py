from analyze_selection_allocation import alpha_interval, summarize


def test_alpha_interval_covers_allocation():
    low, high = alpha_interval(4, 8)
    assert low == 0.4375
    assert high == 0.5625


def test_summarize_selects_collision_and_speed_objectives():
    rows = [
        {
            "k": "4", "front": "0", "suffix": "4", "alpha": "0.0",
            "unique": "8", "collision_entries": "2", "collision_rate": "0.2",
            "collision_pairs": "4", "max_group": "3", "median_seconds": "2.0",
            "throughput_words_per_second": "50.0",
        },
        {
            "k": "4", "front": "2", "suffix": "2", "alpha": "0.5",
            "unique": "9", "collision_entries": "1", "collision_rate": "0.1",
            "collision_pairs": "1", "max_group": "2", "median_seconds": "1.5",
            "throughput_words_per_second": "66.0",
        },
        {
            "k": "4", "front": "4", "suffix": "0", "alpha": "1.0",
            "unique": "9", "collision_entries": "1", "collision_rate": "0.1",
            "collision_pairs": "2", "max_group": "2", "median_seconds": "1.0",
            "throughput_words_per_second": "100.0",
        },
    ]

    result = summarize(rows)
    objectives = {row["objective"]: row for row in result if row["objective"] != "pareto_unique_collision_pairs_throughput"}

    assert objectives["collision_entries"]["front"] == 2
    assert objectives["collision_pairs"]["front"] == 2
    assert objectives["max_group"]["front"] == 2
    assert objectives["throughput_words_per_second"]["front"] == 4
