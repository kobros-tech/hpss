# Experimental Methodology

## 1. Study objective

This study evaluates **Hybrid Prefix-Suffix Selection (HPSS)** as a compact textual representation strategy. The central question is not whether a particular hash function is universally superior, but how much distinguishability is retained when a fixed number of characters is selected from different positions in a key.

The study tests whether the balanced HPSS allocation is optimal, whether the generalized ratio formulation is useful as a parameterization of the allocation family, and whether the preferred allocation depends on the statistical structure of the input keys and on the metric being optimized.

## 2. Experimental pipeline

For every normalized input key `w`:

```text
w -> selector R(w,k) -> representation collision analysis -> encoder -> hash collision analysis
```

The representation and hash stages are intentionally measured separately.

A representation collision means that information has already been lost by selection. A downstream hash function cannot recover this loss.

## 3. HPSS definition

For `len(w) <= k`, HPSS returns `w` unchanged.

For `len(w) > k`:

```text
front = floor(k / 2)
back  = k - front
HPSS(w,k) = w[:front] + w[-back:]
```

Thus:

| k | Front | Back |
|---:|---:|---:|
| 2 | 1 | 1 |
| 3 | 1 | 2 |
| 4 | 2 | 2 |
| 5 | 2 | 3 |
| 6 | 3 | 3 |
| 7 | 3 | 4 |

The odd-`k` rule is part of the original algorithm definition and is preserved for reproducibility.

## 4. Generalized ratio formulation

The balanced rule is one member of the more general boundary-allocation family:

```text
R(k,p) = prefix(p) + suffix(k-p),  0 <= p <= k
```

The ratio selector parameterizes this allocation using `alpha`:

```text
k_eff = min(k, len(w))
p = round_half_up(alpha * k_eff)
s = k_eff - p
R(w,k,alpha) = w[:p] + w[-s:]
```

where `0 <= alpha <= 1`.

The implementation uses deterministic half-up rounding to one allocation outcome. Therefore, for a fixed `k`, alpha is not the experimental unit: only `k+1` distinct allocations exist, and multiple alpha values can produce the same allocation. The research benchmark evaluates every distinct allocation and records the alpha value and interval that represent it.

The endpoints have clear interpretations:

- `alpha = 0`: suffix-only;
- `alpha = 1`: prefix-only;
- `alpha = 0.5`: approximately balanced, subject to the rounding rule.

The original balanced selector remains available so that earlier experiments can be reproduced exactly.

## 5. Baselines

The benchmark compares HPSS with:

- `PREFIX`
- `SUFFIX`
- `MIDDLE`

Each selector is evaluated using the same input normalization, target lengths, metrics, and downstream encoders.

## 6. Allocation and ratio experiments

For every `k=2..12`, the experiment evaluates **all** allocations from `0+k` through `k+0`.

The ratio experiment measures each allocation repeatedly and records:

- unique representations;
- collision entries and collision-entry rate;
- collision pairs;
- maximum collision-group size;
- median selector time;
- throughput in words per second.

The analysis then determines separate optima for:

1. maximum unique representations;
2. minimum collision entries;
3. minimum collision pairs;
4. minimum maximum-group size;
5. maximum throughput.

It also computes a Pareto frontier using collision pairs and throughput. This avoids treating one collision metric or one alpha as a universal objective.

## 7. Datasets and controls

The final study uses three ASCII-oriented sources:

### 7.1 English words

The lexical baseline comes from the pinned `dwyl/english-words` source. The source contains 466,550 records before the repository's canonical normalization/deduplication step. The normalized benchmark corpus contains **466,546 records**.

### 7.2 Estonian domains

The identifier dataset is a deterministic **50,000-record ASCII domain sample** obtained from a pinned upstream source commit.

### 7.3 Random ASCII control

A deterministic control contains **50,000** randomly generated **16-character** strings using lowercase ASCII letters and digits. The random generator uses a fixed seed so the control is reproducible.

The primary experiment intentionally remains ASCII-oriented. Unicode and multilingual datasets are outside the scope of this final study rather than being mixed into the same experimental claim.

## 8. Canonical data handling

All benchmark paths use the same dataset normalization layer.

For the ASCII study, records are:

1. decoded as UTF-8;
2. stripped of surrounding whitespace;
3. lowercased;
4. required to contain only ASCII characters;
5. empty records are discarded;
6. duplicate records are removed deterministically while preserving first occurrence order.

This common loader is used by the main benchmark and the research benchmarks so that their results are directly comparable.

## 9. Encoders

### 9.1 HPSS positional encoder

The proposed positional encoder maps each Unicode code point `c` to `ord(c)+1` and uses base `0x110000` in a Python arbitrary-precision integer.

Because every encoded digit is non-zero and lies within the base, the representation is injective over finite strings. It should therefore be interpreted as an **arbitrary-precision encoding**, not as a fixed-width 64-bit hash.

### 9.2 Reference hashes

The benchmark also evaluates:

- FNV-1a 64-bit;
- MurmurHash3 64-bit;
- xxHash64.

Each receives exactly the selected representation encoded as UTF-8.

## 10. Collision metrics

For `n` input records and `U` unique values:

```text
collision_entries = n - U
collision_entry_rate = (n - U) / n
```

For a collision group of frequency `f`:

```text
collision_pairs = f(f-1)/2
```

The experiment records:

- unique representations;
- collision entries;
- collision-entry rate;
- collision pairs;
- maximum collision-group size;
- unique final hash values;
- final hash collision entries/rate/pairs/max group.

These metrics answer different questions. A configuration can affect the number of inputs participating in collisions differently from the number of colliding pairs or the concentration of collisions into large groups. The ratio analysis therefore does not collapse them into a single collision score.

## 11. Final experimental findings

### English words

The exhaustive allocation experiment shows that balanced HPSS is not the best allocation for larger `k`. The direct allocation ablation reports increasingly prefix-heavy allocations, reaching `10+2` at `k=12` under the primary collision/uniqueness comparison.

At `k=12`, balanced HPSS (`6+6`) produces **462,335** unique representations, whereas `10+2` produces **463,579**. Collision pairs decrease from **9,679** to **3,533**.

The ratio analysis adds an important qualification: there is no single collision optimum independent of the metric. Separate analyses are therefore provided for collision entries, collision pairs, maximum collision-group size, and unique representations.

### Estonian domains

The domain sample gives a different result. Prefix-only allocation (`k+0`) is best for every tested `k=2..12` in the final exhaustive allocation sweep.

At `k=12`, `12+0` produces **49,691** unique representations compared with **49,455** for balanced `6+6`.

This demonstrates that the usefulness of suffix information is dependent on the key distribution.

### Random ASCII control

At sufficiently large `k`, the random control produces essentially complete uniqueness for all allocations. Consequently, positional allocation has little practical effect once enough random characters are retained.

### Speed

The ratio experiment performs repeated selector-level timing for every distinct allocation. In the tested environment, prefix-only allocation was the fastest measured allocation for the tested `k` values.

This is a benchmark observation rather than a universal performance claim. Hardware, Python version, system load, and implementation details can affect absolute throughput.

### Trade-off analysis

Collision quality and speed need not favor the same allocation. The Pareto analysis therefore reports configurations for which no other tested allocation simultaneously improves the selected collision metric and throughput.

This is the appropriate interpretation of the ratio parameter: it exposes a discrete family of allocation choices from which a workload-specific trade-off can be selected, rather than defining one universally optimal floating-point constant.

## 12. Hash-collision interpretation

In the final finite benchmark, the representation-stage collision statistics match the statistics observed after FNV-1a, MurmurHash3, and xxHash64. No additional collisions among distinct selected representations were observed for these reference hashes.

This is only an empirical observation for the tested finite datasets. It is not a proof of collision-freedom over the full domains of the fixed-width hash functions.

For the arbitrary-precision HPSS positional encoder, matching collision statistics follow from its injective construction.

## 13. Reproducibility and automation

The repository contains dedicated scripts for the benchmark and ratio analysis. GitHub Actions runs the tests, the established benchmark, the allocation ablations, the exhaustive ratio experiment, and the objective-specific analysis.

The ratio workflow publishes machine-readable result files including:

```text
ratio_experiment.csv
ratio_unique_optima.csv
ratio_collision_entries_optima.csv
ratio_collision_pairs_optima.csv
ratio_max_group_optima.csv
ratio_speed_optima.csv
ratio_pareto_frontier.csv
```

Timing values should be interpreted as environment-specific measurements. The allocation and collision statistics are deterministic for a fixed dataset, normalization procedure, implementation, and configuration.

## 14. Interpretation

The experiments support four narrow conclusions:

1. **Selection matters.** A large fraction of observed collisions can arise before hashing, from the information discarded by the selector.
2. **Balanced HPSS is not universally optimal.** The optimal front/back allocation varies with the dataset and with the collision metric being optimized.
3. **Speed and collision quality can trade off.** Prefix-only selection is fastest in the tested selector benchmark, while more balanced or suffix-retaining allocations can provide different collision behavior.
4. **Dataset structure matters.** English words, real-world ASCII domains, and random ASCII controls produce materially different allocation behavior.

The experiments therefore support HPSS as a **dataset-dependent representation heuristic**, not as a universal replacement for established hash functions.

## 15. Limitations

- The study is finite and empirical.
- The primary input domain is ASCII-oriented.
- Only one lexical dataset and one domain sample are used.
- The random control is synthetic.
- No adversarial-key analysis is included.
- The positional encoder is arbitrary precision rather than fixed-width.
- Timing depends on hardware, runtime, and system load.
- Selector-level speed does not establish end-to-end application performance.
- Alpha parameterizes a discrete allocation family; it should not be interpreted as a continuously optimized quantity.
- Dataset-specific optima should not be treated as universal rules.
