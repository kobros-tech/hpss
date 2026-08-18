# HPSS — Hybrid Prefix-Suffix Selection

**Research code and reproducible benchmark** for studying compact textual representations created by selecting characters from the boundaries of a textual key.

> **Research status:** experimental. The results in this repository do **not** establish HPSS as a universally superior hash function. The primary object of study is the **selection strategy** and the collision behavior it induces before hashing.

## Abstract

HPSS (Hybrid Prefix-Suffix Selection) is a deterministic character-selection strategy that retains characters from both the beginning and end of a key. The original balanced rule allocates `floor(k/2)` characters to the prefix and the remainder to the suffix. For example, `k=5` selects `2+3` characters.

The study separates two fundamentally different phenomena:

1. **Representation collisions** — two different inputs become identical because the selector discards information.
2. **Downstream hash collisions** — distinct selected representations are mapped to the same fixed-width hash value.

The experiments show that these should not be conflated. In the tested datasets, the dominant source of collisions is the representation stage. No additional collisions were observed for FNV-1a, MurmurHash3, or xxHash64 among the distinct representations in the finite benchmark.

The main result is **dataset- and objective-dependent**. On the normalized English-word dataset, the balanced HPSS split is not the best allocation for larger `k`; increasingly prefix-heavy allocations generally perform better. On the 50,000-record ASCII domain sample, prefix-only selection is best for every tested `k`. On the deterministic random ASCII control, allocation has little practical effect once enough characters are retained because the representations are already almost entirely unique.

The ratio extension makes the boundary-allocation family explicit. It represents the allocation as a fraction `alpha` of the effective character budget assigned to the prefix, with the remainder assigned to the suffix. Because allocation is discrete, different alpha values can produce the same prefix/suffix counts for a given `k`. The research analysis therefore reports separate optima for different collision metrics and for speed rather than declaring one universal alpha.

These results support HPSS as an empirical boundary-selection heuristic, not as a universally optimal hashing method.

## Research questions

1. How does compact boundary selection affect representation collisions as `k` increases?
2. How does the balanced HPSS rule compare with PREFIX, SUFFIX, and MIDDLE selection?
3. Is the balanced front/back allocation actually optimal?
4. Does the downstream encoder introduce additional collisions among distinct selected representations?
5. Does the observed allocation behavior depend on the structure of the input dataset?
6. For the generalized ratio formulation, which allocation is preferred under different collision and speed objectives?

## Method

For every normalized key `w`:

```text
w -> selector R(w,k) -> representation statistics -> encoder -> hash statistics
```

For the balanced HPSS rule, when `len(w) > k`:

```text
front = floor(k/2)
back  = k - front
HPSS(w,k) = w[:front] + w[-back:]
```

For short keys (`len(w) <= k`), HPSS returns the complete key unchanged.

The research benchmark also evaluates the general allocation family:

```text
R(k,p) = prefix(p) + suffix(k-p),  0 <= p <= k
```

Every allocation is tested for every `k` from 2 through 12; the balanced HPSS rule is therefore treated as a hypothesis to test rather than an assumption about optimality.

### Ratio formulation

The generalized selector exposes the same discrete allocation through a continuous parameter:

```text
k_eff = min(k, len(w))
p = round_half_up(alpha * k_eff)
s = k_eff - p
```

where `0 <= alpha <= 1`.

Thus:

- `alpha = 0` selects suffix characters only;
- `alpha = 1` selects prefix characters only;
- intermediate values allocate the effective budget between the two boundaries.

The implementation uses deterministic half-up rounding. The original balanced selector remains available for reproducibility of the earlier experiments.

Because only `k+1` distinct allocations exist for a fixed `k`, alpha is not itself the experimental unit: multiple alpha values may map to the same allocation. The ratio experiment therefore evaluates every distinct allocation and reports the corresponding alpha representation/interval.

## Collision taxonomy

If

```text
R(a,k) == R(b,k)
```

for two different inputs, the collision occurred **before hashing**. No downstream hash function can recover the information discarded by the selector.

The benchmark reports:

- unique representations;
- representation collision entries and rate;
- representation collision pairs;
- maximum collision-group size;
- unique final hash values;
- final hash collision entries/rate/pairs/max group.

For a collision group of frequency `f`, the number of colliding pairs is `f(f-1)/2`.

The ratio analysis deliberately treats collision metrics separately. Minimizing collision entries, minimizing collision pairs, and minimizing the maximum collision-group size are different optimization objectives and can select different allocations.

## Encoders

### HPSS positional encoder

The proposed positional encoder maps each Unicode code point `c` to `ord(c)+1` using base `0x110000` and Python arbitrary-precision integers. This encoding is injective over finite strings. It is therefore an **encoding**, not a fixed-width 64-bit hash.

### Reference encoders

The benchmark also evaluates:

- FNV-1a 64-bit
- MurmurHash3 64-bit
- xxHash64

Reference encoders receive the exact selected representation encoded as UTF-8.

## Datasets

The final experiments use three ASCII-oriented datasets/controls:

1. **English words** — the pinned `dwyl/english-words` source, normalized with `strip().lower()` and deduplicated through the canonical dataset loader. The current normalized benchmark contains **466,546 records**.
2. **Estonian Internet Foundation domains** — a deterministic 50,000-record ASCII domain sample from a pinned upstream commit.
3. **Random ASCII control** — 50,000 deterministic 16-character lowercase-alphanumeric strings generated with a fixed seed.

The primary study is deliberately restricted to ASCII-oriented inputs. Unicode and multilingual generalization are outside the scope of the final experiment.

## Main findings

### English words

The exhaustive allocation study shows that the balanced HPSS split is not empirically optimal for larger `k`. The earlier allocation table remains useful as the direct per-`k` ablation, while the ratio analysis adds a second layer: the preferred allocation depends on which collision statistic is being optimized.

For example, at `k=12`, the previously reported collision-pair comparison is:

```text
balanced 6+6  -> 462,335 unique, 9,679 collision pairs
10+2          -> 463,579 unique, 3,533 collision pairs
```

The ratio analysis also shows why a single phrase such as “the collision-optimal alpha” is insufficient: collision entries, collision pairs, and maximum collision-group size are distinct objectives. The repository therefore publishes separate objective-specific optima and a Pareto analysis rather than collapsing them into one score.

The resulting conclusion is not that one alpha is universally optimal. Rather, English favors **prefix-heavy allocations at larger `k`**, while the exact preferred split depends on the collision objective.

### ASCII domains

The domain sample behaves differently. **PREFIX-only (`k+0`) is the best allocation for every tested `k=2..12`** in the final exhaustive sweep. At `k=12`, prefix-only produces **49,691** unique representations versus **49,455** for balanced `6+6`.

This is an important counterexample to any claim that mixing prefix and suffix characters is universally optimal. It demonstrates that positional information depends on the statistical structure of the keys.

### Random ASCII control

The deterministic random strings behave as expected for a structure-free control. Once enough characters are retained, essentially all tested allocations produce unique representations. Consequently, there is little meaningful allocation advantage at larger `k` values.

Together, the three datasets indicate that the observed allocation effect is **distribution-dependent**, rather than an inherent advantage of boundary selection on arbitrary strings.

### Speed and trade-offs

The ratio benchmark measures repeated selector-level timing for every distinct allocation. In the tested environment, prefix-only allocation was the fastest allocation across the tested `k` values. This is a benchmark observation, not a universal performance theorem.

The collision-optimal and speed-optimal allocations do not have to coincide. The ratio analysis therefore also identifies Pareto-optimal configurations, allowing collision behavior to be compared directly with measured throughput instead of forcing a single “best” alpha.

## Hash-collision finding

For the finite benchmark, the collision statistics at the representation stage match the statistics observed after FNV-1a, MurmurHash3, and xxHash64. No additional collisions among distinct selected representations were observed for these reference hashes.

This is an empirical result for the tested finite datasets; it is **not** a proof that these fixed-width hashes are collision-free over their full input domains.

For the arbitrary-precision HPSS positional encoder, equality is structural rather than empirical: the encoding is injective by construction.

## Reproduce

Use Python 3.11+:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python benchmark.py
pytest -q
```

The ratio research experiment can be run directly with the repository's canonical English dictionary:

```bash
python research_ratio_experiment.py \
  --input dictionaries/words.txt \
  --output results/ratio_experiment.csv
```

The corresponding analysis produces objective-specific summaries and the Pareto frontier. GitHub Actions runs the research experiment and publishes the generated CSV files as workflow artifacts.

The research workflows also download the pinned external datasets before running the multi-dataset experiment. The canonical dataset loader is shared by the benchmark and research experiments so that normalization and deduplication cannot silently diverge.

## Repository structure

```text
.
├── hpss_hash.py
├── benchmark.py
├── research_benchmark.py
├── research_datasets.py
├── research_experiments.py
├── research_ratio_experiment.py
├── analyze_ratio_experiment.py
├── allocation_ablation_benchmark.py
├── multi_dataset_allocation_benchmark.py
├── download_research_datasets.py
├── test_hpss.py
├── test_research_datasets.py
├── test_research_experiments.py
├── tests/
│   └── test_ratio_experiment.py
├── dictionaries/
│   ├── words.txt
│   ├── english_words_source.txt
│   └── estonian_domains_source.txt
├── .github/
│   └── workflows/
│       ├── tests.yml
│       └── benchmark.yml
├── RESULTS_fresh.csv
├── RESULTS_METADATA.txt
├── METHODS.md
├── PAPER_OUTLINE.md
├── paper.md
├── paper.bib
├── CITATION.cff
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── SUPPORT.md
├── CHANGELOG.md
└── LICENSE
```

## Limitations

- Results are empirical and dataset-dependent.
- The primary study is restricted to ASCII-oriented inputs.
- Only one independently sourced lexical dataset and one independently sourced domain sample are used.
- The random control is synthetic and is not a substitute for additional real-world workloads.
- Normalization and deduplication affect the measured collision statistics.
- The study does not establish adversarial robustness.
- The positional encoder is arbitrary precision rather than a fixed-width hash.
- Timing depends on hardware, Python version, libraries, and system load.
- Speed results are selector-level benchmark results and should not be generalized to all implementations or hardware.
- Alpha is a convenient parameterization of a discrete allocation family; it should not be interpreted as a continuously optimized physical quantity.
- Dataset-specific optima should not be assumed to generalize to other workloads without testing them.
- Zero observed collisions in a finite benchmark does not prove universal collision resistance for a fixed-width hash.

## Research materials

See [`METHODS.md`](METHODS.md) for the final experimental protocol and [`PAPER_OUTLINE.md`](PAPER_OUTLINE.md) for the paper structure and interpretation.

## License

MIT. See [`LICENSE`](LICENSE).

## Citation

If this software or benchmark is used in academic work, cite the repository using the metadata in [`CITATION.cff`](CITATION.cff).
