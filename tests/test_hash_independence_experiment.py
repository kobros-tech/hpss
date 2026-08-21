from hash_independence_experiment import HASH_FUNCTIONS, SELECTIONS, collision_stats, run


def test_hash_functions_have_expected_families():
    assert {"FNV1A64", "MURMUR3_64", "XXHASH64"} <= HASH_FUNCTIONS.keys()
    assert {"HPSS_POSITIONAL", "SHA256", "SHA3_256"} <= HASH_FUNCTIONS.keys()


def test_selections_are_the_experiment_controls():
    assert SELECTIONS == {"NONE": None, "HPSS": SELECTIONS["HPSS"]}


def test_collision_stats():
    stats = collision_stats([1, 1, 2, 3, 3])
    assert stats["unique"] == 3
    assert stats["collision_entries"] == 2
    assert stats["collision_pairs"] == 2
    assert stats["max_group"] == 2


def test_run_keeps_selection_identical_across_hashes():
    rows = run(["alpha", "alpine", "beta"], [4], repetitions=1)
    by_selection = {}
    for row in rows:
        by_selection.setdefault(row["selection"], set()).add(row["representation_unique"])

    assert by_selection
    assert all(len(values) == 1 for values in by_selection.values())

    expected_rows = len(SELECTIONS) * len(HASH_FUNCTIONS)
    assert len(rows) == expected_rows


def test_hash_collisions_match_representation_collisions():
    rows = run(["alpha", "alpine", "beta"], [4], repetitions=1)
    for row in rows:
        assert row["hash_unique"] == row["representation_unique"]
        assert row["hash_collision_entries"] == row["representation_collision_entries"]
        assert row["hash_collision_pairs"] == row["representation_collision_pairs"]
        assert row["hash_max_group"] == row["representation_max_group"]


def test_no_selection_is_independent_of_k():
    rows = run(["alpha", "alpine", "beta"], [2, 4], repetitions=1)
    none_rows = [row for row in rows if row["selection"] == "NONE"]
    assert {row["representation_unique"] for row in none_rows} == {3}
