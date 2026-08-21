from research_ratio_experiment import bootstrap_ci, percentile


def test_percentile_interpolates():
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5


def test_bootstrap_ci_is_reproducible():
    samples = [1.0, 1.1, 0.9, 1.05, 0.95]
    ci1 = bootstrap_ci(samples, lambda values: sum(values) / len(values), iterations=500, seed=42)
    ci2 = bootstrap_ci(samples, lambda values: sum(values) / len(values), iterations=500, seed=42)
    assert ci1 == ci2
    assert ci1[0] <= 1.0 <= ci1[1]


def test_single_sample_ci_collapses_to_observation():
    assert bootstrap_ci([3.0], lambda values: values[0], iterations=100, seed=1) == (3.0, 3.0)
