# HPSS — Hybrid Prefix-Suffix Selection

**Research code and reproducible benchmark** for studying compact textual representations created by selecting characters from the boundaries of a textual key.

> **Research status:** experimental. The results in this repository do **not** establish HPSS as a universally superior hash function. The primary object of study is the **selection strategy** and the collision behavior it induces before hashing.

## Abstract

HPSS (Hybrid Prefix-Suffix Selection) is a deterministic character-selection strategy that retains characters from both the beginning and end of a key. The original balanced rule allocates `floor(k/2)` characters to the prefix and the remainder to the suffix. For example, `k=5` selects `2+3` characters.

The study separates two fundamentally different phenomena:

1. **Representation collisions** — two different inputs become identical because the selector discards information.
2. **Downstream hash collisions** — distinct selected representations are mapped to the same fixed-width hash value.

The experiments show that these should not be conflated. In the tested datasets, the dominant source of collisions is the representation stage. No additional collisions were observed for FNV-1a, MurmurHash3, or xxHash64 among the distinct representations in the finite benchmark.

The main result is **dataset-dependent**. On the normalized English-word dataset, the balanced HPSS split is not the best allocation for `k >= 4`; increasingly prefix-heavy allocations generally perform better, with `10+2` best at `k=12`. On the 50,000-record ASCII domain sample, prefix-only selection is best for every tested `k`. On the deterministic random ASCII control, allocation has little practical effect once enough characters are retained because the representations are already almost entirely unique.

These results support HPSS as an empirical boundary-selection heuristic, not as a universally optimal hashing method.

## Research questions

1. How does compact boundary selection affect representation collisions as `k` increases?
2. How does the balanced HPSS rule compare with PREFIX, SUFFIX, and MIDDLE selection?
3. Is the balanced front/back allocation actually optimal?
4. Does the downstream encoder introduce additional collisions among distinct selected representations?
5. Does the observed allocation behavior depend on the structure of the input dataset?

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

The balanced HPSS split is not empirically optimal for `k >= 4`. The best allocations in the final exhaustive sweep are:

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
| 12 | **10+2** |

At `k=12`, balanced `6+6` produces **462,335** unique representations, while `10+2` produces **463,579**. The corresponding collision-pair count falls from **9,679** to **3,533**. Thus the allocation itself has a substantial effect on collision structure.

The original balanced HPSS rule nevertheless has a useful property: it consistently combines information from both boundaries and can outperform simple PREFIX and SUFFIX selectors. The experiments show, however, that this does not make the balanced split universally optimal.

### ASCII domains

The domain sample behaves differently. **PREFIX-only (`k+0`) is the best allocation for every tested `k=2..12`** in the final exhaustive sweep. At `k=12`, prefix-only produces **49,691** unique representations versus **49,455** for balanced `6+6`.

This is an important counterexample to any claim that mixing prefix and suffix characters is universally optimal. It demonstrates that positional information depends on the statistical structure of the keys.

### Random ASCII control

The deterministic random strings behave as expected for a structure-free control. Once enough characters are retained, essentially all tested allocations produce unique representations. Consequently, there is little meaningful allocation advantage at larger `k` values.

Together, the three datasets indicate that the observed allocation effect is **distribution-dependent**, rather than an inherent advantage of boundary selection on arbitrary strings.

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

The research workflows also download the pinned external datasets before running the multi-dataset experiment. The canonical dataset loader is shared by the benchmark and research experiments so that normalization and deduplication cannot silently diverge.

## Repository structure

```text
.
├── hpss_hash.py
├── benchmark.py
├── research_datasets.py
├── research_experiments.py
├── multi_dataset_allocation_benchmark.py
├── download_research_datasets.py
├── test_hpss.py
├── test_research_experiments.py
├── dictionaries/
│   ├── words.txt
│   ├── english_words_source.txt
│   └── estonian_domains_source.txt
├── RESULTS_fresh.csv
├── RESULTS_METADATA.txt
├── METHODS.md
├── PAPER_OUTLINE.md
├── CITATION.cff
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
- Zero observed collisions in a finite benchmark does not prove universal collision resistance for a fixed-width hash.

## Research materials

See [`METHODS.md`](METHODS.md) for the final experimental protocol and [`PAPER_OUTLINE.md`](PAPER_OUTLINE.md) for the paper structure and interpretation.

## License

MIT. See [`LICENSE`](LICENSE).

## Citation

If this software or benchmark is used in academic work, cite the repository using the metadata in [`CITATION.cff`](CITATION.cff).
