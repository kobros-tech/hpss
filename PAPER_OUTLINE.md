# HPSS Research Paper

## Title

**Hybrid Prefix-Suffix Selection for Compact ASCII Textual Keys: An Empirical Study of Boundary Allocation and Collision Structure**

## Abstract

Compact representations of textual keys are often constructed by retaining a fixed number of characters before applying a hash or encoding function. This work studies **Hybrid Prefix-Suffix Selection (HPSS)**, a deterministic strategy that retains characters from both boundaries of a key. Rather than assuming that a balanced prefix/suffix split is optimal, we exhaustively evaluate every allocation of a fixed character budget between the two boundaries.

The evaluation separates **representation collisions**, caused by information discarded during selection, from **downstream hash collisions**, caused by the encoder. Experiments cover a normalized 466,546-record English-word corpus, a 50,000-record ASCII domain sample, and a deterministic random-ASCII control. The results show that allocation quality is strongly dataset-dependent. On English words, the balanced HPSS split is not optimal for `k >= 4`, and the best allocation reaches `10+2` at `k=12`, improving unique representations from 462,335 to 463,579 and reducing collision pairs from 9,679 to 3,533. On the domain sample, prefix-only selection is best for every tested `k`. On random ASCII strings, allocation has little practical effect once sufficient characters are retained. No additional collisions were observed among distinct selected representations when processed by FNV-1a, MurmurHash3, or xxHash64 in the finite benchmark.

The results support a narrow conclusion: **the value of boundary selection depends on the statistical structure of the keys**. HPSS should therefore be regarded as a dataset-dependent representation heuristic rather than a universally superior hashing method.

---

## 1. Introduction

### 1.1 Motivation

Applications frequently need compact representations of textual keys. Reducing a key to a fixed number of characters can reduce storage or indexing cost, but it also discards information and can create collisions before any conventional hash function is applied.

This work investigates whether selecting characters from both ends of a key can preserve more distinguishability than simple positional strategies.

### 1.2 The central distinction

A conventional hash collision and a selection collision are different events.

If:

```text
R(a,k) = R(b,k)
```

for distinct keys `a` and `b`, the selector has already made the keys indistinguishable. A downstream hash cannot repair this loss.

The experiments therefore measure representation quality independently from hash behavior.

### 1.3 Research questions

1. How does boundary selection affect collision behavior as the representation budget `k` increases?
2. Does balanced HPSS outperform PREFIX, SUFFIX, and MIDDLE selection?
3. Is a balanced front/back allocation actually optimal?
4. Does the answer depend on the statistical structure of the keys?
5. Do downstream hash functions introduce additional collisions among distinct selected representations?

### 1.4 Contributions

The study contributes:

- a precise definition of the HPSS selection rule;
- a separation of representation and downstream hash collisions;
- exhaustive front/back allocation ablation rather than an assumed 50/50 split;
- a reproducible comparison across lexical, real-world identifier, and random ASCII inputs;
- an empirical demonstration that the optimal allocation is dataset-dependent.

---

## 2. Method

### 2.1 HPSS

For a key `w` and target length `k`, if `len(w) <= k`, the key is returned unchanged.

Otherwise:

```text
front = floor(k/2)
back  = k - front
HPSS(w,k) = w[:front] + w[-back:]
```

For odd `k`, the extra character goes to the suffix.

### 2.2 General allocation family

To test the balanced assumption directly, define:

```text
R(k,p) = prefix(p) + suffix(k-p)
```

where `p` ranges from `0` through `k`.

Thus the experiment includes PREFIX-only, SUFFIX-only, balanced HPSS, and every intermediate allocation.

### 2.3 Baselines

The principal selectors are:

- PREFIX;
- SUFFIX;
- MIDDLE;
- balanced HPSS;
- all front/back allocations in the ablation experiment.

### 2.4 Downstream encoders

The study evaluates the proposed arbitrary-precision positional encoder and three established fixed-width hash functions:

- FNV-1a 64-bit;
- MurmurHash3 64-bit;
- xxHash64.

The positional encoder is an injective encoding over finite strings and is therefore not treated as a fixed-width hash competitor.

---

## 3. Experimental Design

### 3.1 Dataset normalization

All experiments use a common canonical loader. Records are stripped, lowercased, restricted to ASCII for the primary study, and deduplicated deterministically.

The final English corpus contains 466,546 normalized records.

### 3.2 Datasets

**English words:** pinned `dwyl/english-words` source.

**ASCII domains:** deterministic 50,000-record sample from a pinned Estonian Internet Foundation domain source.

**Random ASCII:** 50,000 deterministic 16-character lowercase-alphanumeric strings generated from a fixed seed.

The primary study intentionally does not mix Unicode/multilingual inputs into the ASCII evaluation.

### 3.3 Tested representation sizes

```text
k = 2,3,4,5,6,7,8,9,10,11,12
```

### 3.4 Metrics

For each selector and allocation, report:

- unique representations;
- collision entries;
- collision-entry rate;
- collision pairs;
- maximum collision-group size;
- unique downstream hash values;
- downstream collision entries/rate/pairs/max group.

### 3.5 Reproducibility

Dataset sources are pinned, synthetic controls use fixed seeds, and the same canonical loader is used across benchmark paths. The repository records benchmark metadata and dependencies.

---

## 4. Results

### 4.1 English words

The exhaustive allocation experiment shows that balanced HPSS is not the best allocation for `k >= 4`.

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

At `k=12`:

```text
balanced 6+6  -> 462,335 unique, 9,679 collision pairs
best 10+2     -> 463,579 unique, 3,533 collision pairs
```

The difference is not merely a small change in the number of unique values: the collision-pair count falls substantially under the best allocation.

### 4.2 ASCII domains

The domain sample gives a different result. Prefix-only allocation (`k+0`) is best for every tested `k`.

At `k=12`:

```text
balanced 6+6  -> 49,455 unique
prefix 12+0   -> 49,691 unique
```

This is a direct counterexample to the idea that retaining both boundaries is always preferable.

### 4.3 Random ASCII control

For sufficiently large `k`, essentially all tested allocations produce unique representations in the random control. This means that the allocation differences observed in structured datasets are not reproduced when the input distribution lacks comparable structure.

### 4.4 Downstream hashes

For the finite benchmark, the representation-stage collision statistics are unchanged after FNV-1a, MurmurHash3, and xxHash64. No additional collisions among distinct selected representations were observed.

This should be reported as an empirical finite-sample result, not as a universal collision guarantee.

---

## 5. Discussion

### 5.1 The balanced HPSS hypothesis

The experiments reject the narrow hypothesis that a balanced split is generally optimal. On English words, asymmetric allocations perform better at larger representation budgets. On domains, prefix-only selection performs best.

### 5.2 Dataset dependence

The strongest common observation across the experiments is that positional information is distribution-dependent.

English words contain linguistic regularities that make both boundaries informative, but the information is not equally distributed between them. Domain names have different positional structure, and the prefix contains enough information in the tested sample that adding suffix characters is counterproductive at the measured budget. Random strings do not exhibit a comparable positional structure.

### 5.3 What the study does not show

The experiments do **not** show that HPSS is a better general-purpose hash function than established hashes.

They also do not establish a universal optimal allocation such as `10+2`. That allocation is the best observed for one tested corpus at `k=12`; it should not be generalized to other workloads without evidence.

### 5.4 Representation versus hashing

The experiments reinforce the importance of measuring selection collisions separately. Once information is discarded by a selector, a downstream hash cannot restore it. Conversely, a hash function should not be blamed for collisions that already existed in the selected representation.

---

## 6. Limitations

- The study is finite and empirical.
- The primary study is ASCII-oriented.
- Only one lexical corpus and one domain sample are used.
- The random control is synthetic.
- No adversarial-key analysis is included.
- The positional encoder is arbitrary precision rather than fixed-width.
- Timing is environment-dependent.
- Dataset-specific optima should not be treated as universal rules.

---

## 7. Conclusion

HPSS provides a simple way to construct compact representations from the boundaries of textual keys, but the experiments do not support a universal claim of superiority.

The main empirical finding is more specific: **the optimal allocation of a fixed character budget between the beginning and end of a key depends on the statistical structure of the key distribution**.

For the tested English corpus, balanced HPSS is not optimal at larger `k`, and increasingly prefix-heavy allocations perform better. For the tested ASCII domain sample, prefix-only selection is consistently best. For random ASCII strings, allocation matters little once enough characters are retained.

These findings motivate treating HPSS as a representation heuristic whose parameters should be evaluated against the intended key distribution, rather than as a universally optimal hashing construction.

---

## 8. Reproducibility

The repository contains the implementation, tests, pinned dataset provenance, benchmark scripts, metadata, and CI configuration used to produce the reported results.

The recommended validation command is:

```bash
pytest -q
```

The benchmark and research workflows should be rerun when changing algorithm code, dataset sources, normalization, dependencies, or experimental configuration.
