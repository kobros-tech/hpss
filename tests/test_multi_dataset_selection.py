from analyze_multi_dataset_selection import alpha_interval, analyze


def row(dataset: str, k: int, front: int, unique: int, entries: int, pairs: int, max_group: int) -> dict[str, str]:
    return {
        "dataset": dataset,
        "k": str(k),
        "front": str(front),
        "back": str(k - front),
        "allocation": f"{front}+{k-front}",
        "records": "100",
        "unique": str(unique),
        "unique_rate": str(unique / 100),
        "collision_entries": str(entries),
        "collision_pairs": str(pairs),
        "max_group": str(max_group),
        "is_balanced_hpss": "0",
        "is_best_unique": "0",
    }


def test_alpha_interval_uses_half_up_boundaries():
    assert alpha_interval(0, 4) == (0.0, 0.125)
    assert alpha_interval(1, 4) == (0.125, 0.375)
    assert alpha_interval(4, 4) == (0.875, 1.0)


def test_analysis_selects_metric_specific_allocations():
    rows = [
        row("toy", 4, 0, 80, 10, 20, 5),
        row("toy", 4, 2, 70, 20, 30, 6),
        row("toy", 4, 4, 90, 5, 40, 8),
    ]
    outputs = analyze(rows)

    assert outputs["unique_optima"][0]["front"] == "4"
    assert outputs["collision_entries_optima"][0]["front"] == "4"
    assert outputs["collision_pairs_optima"][0]["front"] == "0"
    assert outputs["max_group_optima"][0]["front"] == "0"


def test_balanced_comparison_reports_gap_from_best():
    rows = [
        row("toy", 4, 0, 80, 10, 20, 5),
        row("toy", 4, 2, 70, 20, 30, 6),
        row("toy", 4, 4, 90, 5, 40, 8),
    ]
    comparison = analyze(rows)["balanced_comparison"][0]
    assert comparison["best_unique"] == "90"
    assert comparison["best_unique_allocations"] == "4+0"
    assert comparison["best_unique_allocation_count"] == "1"
    assert comparison["unique_gap_from_best"] == 20
    assert comparison["is_balanced_best_unique"] == "0"


def test_balanced_comparison_preserves_tied_best_allocations():
    rows = [
        row("toy", 4, 0, 100, 10, 20, 5),
        row("toy", 4, 1, 100, 10, 20, 5),
        row("toy", 4, 2, 90, 20, 30, 6),
        row("toy", 4, 3, 100, 10, 20, 5),
        row("toy", 4, 4, 80, 30, 40, 7),
    ]
    comparison = analyze(rows)["balanced_comparison"][0]
    assert comparison["best_unique"] == "100"
    assert comparison["best_unique_allocations"] == "0+4;1+3;3+1"
    assert comparison["best_unique_allocation_count"] == "3"
    assert comparison["unique_gap_from_best"] == 10
    assert comparison["is_balanced_best_unique"] == "0"
