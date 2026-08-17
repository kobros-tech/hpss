# Experimental Methodology

## 1. Study objective

This study evaluates **Hybrid Prefix-Suffix Selection (HPSS)** as a compact textual representation strategy. The central question is not whether a particular hash function is universally superior, but how much distinguishability is retained when a fixed number of characters is selected from different positions in a key.

The final experiment also asks whether the balanced HPSS allocation is actually optimal and whether the answer depends on the statistical structure of the input keys.

## 2. Experimental pipeline

For every normalized input key `w`:

```text
w -> selector R(w,k) -> representation collision analysis -> encoder -> hash collision analysis
```

The representation and hash stages are intentionally measured separately.

A representation collision means that information has already been lost by selection. A downstream hash function cannot recover that information.

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

The odd-`k` rule is part of the algorithm definition.

## 4. Baselines

The benchmark compares HPSS with:

- `PREFIX`
- `SUFFIX`
- `MIDDLE`

Each selector is evaluated using the same input normalization, target lengths, metrics, and downstream encoders.

## 5. Allocation ablation

Balanced HPSS is only one member of the more general boundary-allocation family:

```text
R(k,p) = prefix(p) + suffix(k-p),  0 <= p <= k
```

For every `k=2..12`, the experiment evaluates **all** allocations from `0+k` through `k+0`.

This avoids assuming that a 50/50 split is optimal.

The final English results show that it is not: for `k >= 4`, the best allocation is generally asymmetric, reaching `10+2` at `k=12`. The domain results provide a stronger counterexample: prefix-only selection is best for every tested `k` in that dataset.

## 6. Datasets and controls

The final study uses three ASCII-oriented sources:

### 6.1 English words

The lexical baseline comes from the pinned `dwyl/english-words` source. The source contains 466,550 records before the repository's canonical normalization/deduplication step. The normalized benchmark corpus contains **466,546 records**.

### 6.2 Estonian domains

The identifier dataset is a deterministic **50,000-record ASCII domain sample** obtained from a pinned upstream source commit.

### 6.3 Random ASCII control

A deterministic control contains **50,000** randomly generated **16-character** strings using lowercase ASCII letters and digits. The random generator uses a fixed seed so the control is reproducible.

The primary experiment intentionally remains ASCII-oriented. Unicode and multilingual datasets are outside the scope of this final study rather than being mixed into the same experimental claim.

## 7. Canonical data handling

All benchmark paths use the same dataset normalization layer.

For the ASCII study, records are:

1. decoded as UTF-8;
2. stripped of surrounding whitespace;
3. lowercased;
4. required to contain only ASCII characters;
5. empty records are discarded;
6. duplicate records are removed deterministically while preserving first occurrence order.

This common loader is used by the main benchmark and the research benchmarks so that their results are directly comparable.

## 8. Encoders

### 8.1 HPSS positional encoder

The proposed positional encoder maps each Unicode code point `c` to `ord(c)+1` and uses base `0x110000` in a Python arbitrary-precision integer.

Because every encoded digit is non-zero and lies within the base, the representation is injective over finite strings. It should therefore be interpreted as an **arbitrary-precision encoding**, not as a fixed-width 64-bit hash.

### 8.2 Reference hashes

The benchmark also evaluates:

- FNV-1a 64-bit;
- MurmurHash3 64-bit;
- xxHash64.

Each receives exactly the selected representation encoded as UTF-8.

## 9. Collision metrics

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

## 10. Final experimental results

### English words

The best allocation for each `k` was:

| k | Best allocation |
|---:|---:|
| 2 | 1+1 |
| 3 | 1+2 |
| 4 | 1+3 |
| 5 | 4+1 |
| 6 | 4+2 |
| 7 | 5+2 |
| 8 | 6+2 |
| 9 | 7+2 |
| 10 | 8+2 |
| 11 | 9+2 |
| 12 | 10+2 |

At `k=12`, balanced HPSS (`6+6`) produces **462,335** unique representations, whereas `10+2` produces **463,579**. Collision pairs decrease from **9,679** to **3,533**.

The result demonstrates that the balanced HPSS rule is a useful boundary-selection strategy but is not the optimal allocation for this corpus.

### Estonian domains

The best allocation is `k+0` (PREFIX-only) for every tested `k=2..12`.

At `k=12`, `12+0` produces **49,691** unique representations compared with **49,455** for balanced `6+6`.

This demonstrates that the usefulness of suffix information is dependent on the key distribution.

### Random ASCII control

At sufficiently large `k`, the random control produces essentially complete uniqueness for all allocations. Consequently, positional allocation has little practical effect once enough random characters are retained.

This control provides evidence against interpreting the English result as a universal property of boundary selection over arbitrary strings.

## 11. Hash-collision interpretation

In the final finite benchmark, the representation-stage collision statistics match the statistics observed after FNV-1a, MurmurHash3, and xxHash64. No additional collisions among distinct selected representations were observed for these reference hashes.

This is only an empirical observation for the tested finite datasets. It is not a proof of collision-freedom over the full domains of the fixed-width hash functions.

For the arbitrary-precision HPSS positional encoder, matching collision statistics follow from its injective construction.

## 12. Timing

The benchmark reports throughput for the encoder stage. Timing is environment-dependent and is not treated as a universal performance ranking.

## 13. Interpretation

The experiments support three narrow conclusions:

1. **Selection matters.** A large fraction of observed collisions can arise before hashing, from the information discarded by the selector.
2. **Balanced HPSS is not universally optimal.** The optimal front/back allocation varies with the dataset and, on English words, becomes strongly asymmetric at larger `k`.
3. **Dataset structure matters.** English words, real-world ASCII domains, and random ASCII controls produce materially different allocation behavior.

The experiments therefore support HPSS as a **dataset-dependent representation heuristic**, not as a universal replacement for established hash functions.

## 14. Limitations

- The study is finite and empirical.
- The primary input domain is ASCII-oriented.
- Only one lexical dataset and one domain sample are used.
- The random control is synthetic.
- No adversarial-key analysis is included.
- The positional encoder is arbitrary precision rather than fixed-width.
- Timing depends on hardware, runtime, and system load.
- The measured optimum for a dataset should not be assumed to generalize to other workloads without testing them.
