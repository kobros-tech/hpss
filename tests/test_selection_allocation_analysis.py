from analyze_selection_allocation import alpha_interval, summarize
from research_ratio_experiment import bootstrap_ci


def test_alpha_interval_covers_allocation():
    low, high = alpha_interval(4, 8)
    assert low == 0.4375
    assert high == 0.5625


def test_alpha_intervals_cover_discrete_allocations():
    intervals = [alpha_interval(front, 8) for front in range(9)]
    assert intervals[0][0] == 0.0
    assert intervals[-1][1] == 1.0
    for left, right in zip(intervals, intervals[1:]):
        assert left[1] == right[0]


def test_bootstrap_ci_is_deterministic():
    samples = [1.0, 1.1, 0.9, 1.05, 0.95]
    first = bootstrap_ci(samples, lambda values: sum(values) / len(values), iterations=500, seed=7)
    second = bootstrap_ci(samples, lambda values: sum(values) / len(values), iterations=500, seed=7)
    assert first == second
    assert first[0] <= 1.0 <= first[1]


def test_summarize_selects_collision_and_speed_objectives():
    rows = [
        {
            "k": "4", "front": "0", "suffix": "4", "alpha": "0.0",
            "unique": "8", "collision_entries": "2", "collision_rate": "0.2",
            "collision_pairs": "4", "max_group": "3", "median_seconds": "2.0",
            "timing_iqr_seconds": "0.2", "timing_ci95_low": "1.8",
            "timing_ci95_high": "2.2", "throughput_words_per_second": "50.0",
            "throughput_ci95_low": "45.0", "throughput_ci95_high": "55.0",
            "timing_repeats": "15",
        },
        {
            "k": "4", "front": "2", "suffix": "2", "alpha": "0.5",
            "unique": "9", "collision_entries": "1", "collision_rate": "0.1",
            "collision_pairs": "1", "max_group": "2", "median_seconds": "1.5",
            "timing_iqr_seconds": "0.1", "timing_ci95_low": "1.4",
            "timing_ci95_high": "1.6", "throughput_words_per_second": "66.0",
            "throughput_ci95_low": "62.0", "throughput_ci95_high": "70.0",
            "timing_repeats": "15",
        },
        {
            "k": "4", "front": "4", "suffix": "0", "alpha": "1.0",
            "unique": "9", "collision_entries": "1", "collision_rate": "0.1",
            "collision_pairs": "2", "max_group": "2", "median_seconds": "1.0",
            "timing_iqr_seconds": "0.1", "timing_ci95_low": "0.9",
            "timing_ci95_high": "1.1", "throughput_words_per_second": "100.0",
            "throughput_ci95_low": "95.0", "throughput_ci95_high": "105.0",
            "timing_repeats": "15",
        },
    ]

    result = summarize(rows)
    objectives = {
        row["objective"]: row
        for row in result
        if row["objective"] != "pareto_unique_collision_pairs_throughput"
    }

    assert objectives["collision_entries"]["front"] == 2
    assert objectives["collision_pairs"]["front"] == 2
    assert objectives["max_group"]["front"] == 2
    assert objectives["throughput_words_per_second"]["front"] == 4
    assert objectives["throughput_words_per_second"]["throughput_ci95_low"] == 95.0
