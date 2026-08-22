from four_way_ablation import ALL_HASHES, K_VALUES, run


def test_four_way_ablation_covers_all_configurations() -> None:
    datasets = {"toy": ["alphabet", "almanac", "algebra", "beta", "betamax"]}
    rows = run(datasets, repetitions=1)

    assert len(rows) == len(K_VALUES) * len(ALL_HASHES) * 2
    assert {row["configuration"] for row in rows} == {"A", "B", "C", "D"}
    assert {row["hash"] for row in rows} == set(ALL_HASHES)


def test_selection_changes_representation_but_not_hash_independent_structure() -> None:
    datasets = {"toy": ["alphabet", "almanac", "algebra", "beta", "betamax"]}
    rows = run(datasets, repetitions=1)

    for k in K_VALUES:
        selected = [
            row for row in rows
            if row["k"] == k and row["selection"] == "HPSS"
        ]
        assert selected
        representation = {
            (
                row["representation_unique"],
                row["representation_collision_entries"],
                row["representation_collision_pairs"],
                row["representation_max_group"],
            )
            for row in selected
        }
        assert len(representation) == 1


def test_four_way_mapping_is_explicit() -> None:
    datasets = {"toy": ["abcdef", "abcxyz", "uvwxyz"]}
    rows = run(datasets, repetitions=1)

    assert {row["configuration"] for row in rows if row["hash"] == "HPSS_POSITIONAL"} == {"C", "D"}
    assert {row["configuration"] for row in rows if row["hash"] == "XXHASH64"} == {"A", "B"}
