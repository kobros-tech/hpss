from hpss_hash_experiment import HASH_FUNCTIONS, collision_stats, hpss_positional_hash, make_random_ascii_dataset, run


MASK64 = (1 << 64) - 1


def test_hash_function_families():
    assert {
        "HPSS_POSITIONAL",
        "FNV1A64",
        "MURMUR3_64",
        "XXHASH64",
        "SHA256",
        "SHA3_256",
    } == set(HASH_FUNCTIONS)


def test_collision_stats():
    stats = collision_stats([1, 1, 2, 3, 3])
    assert stats["unique"] == 3
    assert stats["collision_entries"] == 2
    assert stats["collision_pairs"] == 2
    assert stats["max_group"] == 2


def test_random_dataset_is_reproducible_and_unique():
    first = make_random_ascii_dataset(count=100, length=8, seed=7)
    second = make_random_ascii_dataset(count=100, length=8, seed=7)
    assert first == second
    assert len(first) == len(set(first)) == 100


def test_run_evaluates_original_input_without_selection():
    rows = run({"toy": ["alpha", "alpine", "beta"]}, repetitions=1)
    assert len(rows) == len(HASH_FUNCTIONS)
    assert {row["records"] for row in rows} == {3}
    assert {row["unique"] for row in rows} == {3}
    assert all(row["timing_repetitions"] == 1 for row in rows)


def test_hpss_positional_is_64_bit():
    values = [hpss_positional_hash("a" * length) for length in range(1, 100)]
    assert all(0 <= value <= MASK64 for value in values)


def test_hpss_positional_has_no_collision_on_toy_input():
    rows = run({"toy": ["alpha", "alpine", "beta"]}, repetitions=1)
    hpss = next(row for row in rows if row["hash"] == "HPSS_POSITIONAL")
    assert hpss["collision_entries"] == 0
    assert hpss["collision_pairs"] == 0
    assert hpss["max_group"] == 1
