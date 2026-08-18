# HPSS Research Paper

## Title

**Hybrid Prefix-Suffix Selection for Compact ASCII Textual Keys: An Empirical Study of Boundary Allocation, Collision Structure, and Speed Trade-offs**

## Abstract

Compact representations of textual keys are often constructed by retaining a fixed number of characters before applying an encoding or hash. This work studies **Hybrid Prefix-Suffix Selection (HPSS)**, a deterministic strategy that retains characters from both boundaries of a key. Rather than assuming that a balanced prefix/suffix split is optimal, we exhaustively evaluate every allocation of a fixed character budget between the two boundaries and parameterize the allocation with a ratio `alpha`.

The evaluation separates **representation collisions**, caused by information discarded during selection, from **downstream hash collisions**, caused by fixed-width hash functions. Experiments cover a normalized 466,546-record English-word corpus, a 50,000-record ASCII domain sample, and a deterministic random-ASCII control. The results show that allocation quality is dataset- and objective-dependent. On English words, balanced HPSS is not optimal for larger `k`, and prefix-heavy allocations perform better. On the domain sample, prefix-only selection is best for every tested `k`. On random ASCII strings, allocation has little practical effect once sufficient characters are retained. The ratio experiment further shows that collision entries, collision pairs, maximum collision-group size, and speed can favor different allocations, so there is no scientifically justified universal alpha from these experiments alone.

No additional collisions were observed among distinct selected representations when processed by FNV-1a, MurmurHash3, or xxHash64 in the finite benchmark. This is a finite-sample observation rather than a proof of universal collision-freedom.

The results support a narrow conclusion: **the value of boundary selection depends on the statistical structure of the keys and on the objective being optimized**. HPSS should therefore be regarded as a dataset-dependent representation heuristic rather than a universally superior hashing method.

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
6. Does a ratio parameter provide a useful parameterization of the allocation family?
7. Which allocation is preferred when unique representations, collision entries, collision pairs, maximum collision-group size, or speed are the optimization objective?

### 1.4 Contributions

The study contributes:

- a precise definition of the HPSS selection rule;
- a generalized ratio parameterization of prefix/suffix allocation;
- a separation of representation and downstream hash collisions;
- exhaustive front/back allocation ablation rather than an assumed 50/50 split;
- objective-specific analysis of unique representations, collision entries, collision pairs, maximum collision-group size, and selector throughput;
- a Pareto analysis of collision-pair behavior versus speed;
- a reproducible comparison across lexical, real-world identifier, and random ASCII inputs;
- an empirical demonstration that the preferred allocation is dataset- and objective-dependent.

The contribution is deliberately framed as a **representation and experimental methodology contribution**, not as a claim that HPSS replaces established hash functions.

---

## 2. Statement of Need and Software Significance

The software provides a small, reproducible research implementation for studying boundary-based textual selection and the collision consequences of compacting textual keys before hashing or encoding.

The practical research need is to distinguish information loss introduced by a representation strategy from collisions introduced by a downstream fixed-width hash. Existing hash-function comparisons can obscure this distinction because both effects appear together in final hash counts.

HPSS addresses this need by providing:

- deterministic prefix/suffix selectors;
- configurable allocation budgets;
- explicit separation of representation and hash collision statistics;
- multiple reference hash functions;
- exhaustive allocation experiments;
- reproducible dataset loading and provenance;
- automated statistical analysis and CI artifacts.

The software is intended as a research tool and experimental reference implementation. It is not presented as a cryptographic primitive or as a replacement for established general-purpose hashes.

---

## 3. State of the Field

The final manuscript should position HPSS against at least four neighboring areas:

1. **General-purpose non-cryptographic hashing** — e.g. FNV-1a, MurmurHash-family functions, and xxHash, which hash complete inputs into fixed-width outputs.
2. **String fingerprints and compact identifiers** — methods that deliberately reduce textual inputs before storage, indexing, or comparison.
3. **Substring/prefix/suffix indexing and string-search techniques** — methods that exploit positional information from textual keys.
4. **Collision-aware representation and hashing studies** — work that evaluates distinguishability before and after hashing.

The final paper should cite the primary references for the established hash functions and the most closely related representation/indexing methods, then explain the narrower contribution of HPSS: an explicit, reproducible study of **boundary allocation before hashing**, including exhaustive allocation ablation and separate collision objectives.

This section should be completed with verified scholarly and software references before JOSS submission. It should not claim novelty merely because prefix/suffix selection itself is simple; the novelty claim should focus on the defined HPSS formulation, experimental decomposition, allocation analysis, and reproducible research software where supported by the literature review.

---

## 4. Method

### 4.1 HPSS

For a key `w` and target length `k`, if `len(w) <= k`, the key is returned unchanged.

Otherwise:

```text
front = floor(k/2)
back  = k - front
HPSS(w,k) = w[:front] + w[-back:]
```

For odd `k`, the extra character goes to the suffix. This original rule remains unchanged for reproducibility.

### 4.2 General allocation family

To test the balanced assumption directly, define:

```text
R(k,p) = prefix(p) + suffix(k-p)
```

where `p` ranges from `0` through `k`.

Thus the experiment includes PREFIX-only, SUFFIX-only, balanced HPSS, and every intermediate allocation.

### 4.3 Ratio formulation

The generalized selector expresses the allocation using `alpha`:

```text
k_eff = min(k, len(w))
p = round_half_up(alpha * k_eff)
s = k_eff - p
```

where `0 <= alpha <= 1`.

`alpha=0` is suffix-only, `alpha=1` is prefix-only, and intermediate values allocate the effective budget between the two boundaries.

Because allocation is discrete, alpha is a parameterization rather than an independent experimental degree of freedom: for a fixed `k`, there are only `k+1` distinct allocation outcomes. The experiment therefore evaluates allocations exhaustively and reports the alpha value/interval corresponding to each outcome.

### 4.4 Baselines

The principal selectors are:

- PREFIX;
- SUFFIX;
- MIDDLE;
- balanced HPSS;
- all front/back allocations in the ablation experiment.

### 4.5 Encoders and hashes

The study evaluates the proposed arbitrary-precision positional encoder and three established fixed-width hash functions:

- FNV-1a 64-bit;
- MurmurHash3 64-bit;
- xxHash64.

The positional encoder is an injective encoding over finite strings and is therefore not treated as a fixed-width hash competitor.

---

## 5. Experimental Design

### 5.1 Dataset normalization

All experiments use a common canonical loader. Records are stripped, lowercased, restricted to ASCII for the primary study, and deduplicated deterministically.

The final English corpus contains 466,546 normalized records.

### 5.2 Datasets

**English words:** pinned `dwyl/english-words` source.

**ASCII domains:** deterministic 50,000-record sample from a pinned Estonian Internet Foundation domain source.

**Random ASCII:** 50,000 deterministic 16-character lowercase-alphanumeric strings generated from a fixed seed.

The primary study intentionally does not mix Unicode/multilingual inputs into the ASCII evaluation.

### 5.3 Tested representation sizes

```text
k = 2,3,4,5,6,7,8,9,10,11,12
```

### 5.4 Metrics

For each selector and allocation, report:

- unique representations;
- collision entries;
- collision-entry rate;
- collision pairs;
- maximum collision-group size;
- unique downstream hash values;
- downstream collision entries/rate/pairs/max group.

The ratio experiment additionally reports repeated selector timing and throughput in words per second. Separate objective-specific analyses determine the best allocation under each metric rather than treating one metric as a universal definition of “collision quality.”

### 5.5 Ratio experiment and Pareto analysis

For each `k`, every distinct allocation `p=0..k` is benchmarked repeatedly. The experiment records the canonical alpha value associated with that allocation, its alpha interval under the half-up rule, collision statistics, and selector throughput.

The analysis generates:

```text
ratio_experiment.csv
ratio_unique_optima.csv
ratio_collision_entries_optima.csv
ratio_collision_pairs_optima.csv
ratio_max_group_optima.csv
ratio_speed_optima.csv
ratio_pareto_frontier.csv
```

The Pareto analysis uses collision pairs and throughput. A configuration is Pareto-optimal when no other tested allocation simultaneously improves both quantities.

### 5.6 Reproducibility

Dataset sources are pinned, synthetic controls use fixed seeds, and the same canonical loader is used across benchmark paths. The repository records benchmark metadata and dependencies. GitHub Actions runs the ratio experiment and analysis and publishes the machine-readable result files as workflow artifacts.

---

## 6. Results

### 6.1 English words

The exhaustive allocation experiment shows that balanced HPSS is not the best allocation for larger `k`.

The direct allocation ablation reports increasingly prefix-heavy allocations, reaching `10+2` at `k=12` under the primary uniqueness/collision comparison.

At `k=12`:

```text
balanced 6+6  -> 462,335 unique, 9,679 collision pairs
10+2          -> 463,579 unique, 3,533 collision pairs
```

The ratio analysis adds an important qualification: the optimum depends on which collision metric is selected. Collision entries, collision pairs, maximum collision-group size, unique representations, and speed are therefore reported separately.

### 6.2 ASCII domains

The domain sample gives a different result. Prefix-only allocation (`k+0`) is best for every tested `k`.

At `k=12`:

```text
balanced 6+6  -> 49,455 unique
prefix 12+0   -> 49,691 unique
```

This is a direct counterexample to the idea that retaining both boundaries is always preferable.

### 6.3 Random ASCII control

For sufficiently large `k`, essentially all tested allocations produce unique representations in the random control. This means that the allocation differences observed in structured datasets are not reproduced when the input distribution lacks comparable positional structure.

### 6.4 Speed and trade-offs

The ratio experiment measures repeated selector-level timing for every distinct allocation. Prefix-only allocation is the fastest measured allocation in the tested environment across the tested `k` values.

The collision-optimal and speed-optimal allocations need not coincide. The Pareto frontier therefore provides a more useful description of the trade-off than a single recommended alpha.

### 6.5 Downstream hashes

For the finite benchmark, the representation-stage collision statistics are unchanged after FNV-1a, MurmurHash3, and xxHash64. No additional collisions among distinct selected representations were observed.

This should be reported as a finite-sample empirical result, not as a universal collision guarantee.

---

## 7. Discussion

### 7.1 The balanced HPSS hypothesis

The experiments reject the narrow hypothesis that a balanced split is generally optimal. On English words, asymmetric allocations perform better at larger representation budgets. On domains, prefix-only selection performs best.

### 7.2 Dataset and objective dependence

The strongest common observation across the experiments is that positional information is distribution-dependent.

English words contain linguistic regularities that make both boundaries informative, but the information is not equally distributed between them. Domain names have different positional structure, and the prefix contains enough information in the tested sample that adding suffix characters is counterproductive at the measured budget. Random strings do not exhibit a comparable positional structure.

The ratio experiment adds a second qualification: “best” depends on the objective. An allocation that reduces the number of input records participating in collisions need not minimize the number of colliding pairs, and an allocation with better collision structure need not maximize selector throughput.

### 7.3 The role of alpha

The experiments do not justify treating a value such as `alpha=0.76` as a universal constant. Alpha is best understood as a convenient parameterization of the discrete prefix/suffix allocation family.

A workload can choose an allocation based on its objective and empirical distribution. The repository provides the machinery to measure that choice rather than embedding a universal optimum into the algorithm.

### 7.4 What the study does not show

The experiments do **not** show that HPSS is a better general-purpose hash function than established hashes.

They also do not establish a universal optimal allocation such as `10+2`. That allocation is the best observed under a particular metric for one tested corpus and representation size; it should not be generalized to other workloads without evidence.

### 7.5 Representation versus hashing

The experiments reinforce the importance of measuring selection collisions separately. Once information is discarded by a selector, a downstream hash cannot restore it. Conversely, a hash function should not be blamed for collisions that already existed in the selected representation.

---

## 8. Software Design and Research Impact

The software is deliberately organized around reproducibility rather than production-scale hashing claims. The implementation, dataset loader, benchmark scripts, allocation sweep, ratio experiment, statistical analysis, tests, and GitHub Actions workflow form a single research pipeline.

The intended research impact is to make boundary-based textual representation choices measurable and reproducible. A researcher can change the dataset, representation budget, allocation, or downstream hash and inspect the resulting collision structure without rewriting the experimental framework.

The manuscript should report this as the principal software contribution rather than claiming that the package establishes a new universal hashing standard.

---

## 9. Limitations

- The study is finite and empirical.
- The primary study is ASCII-oriented.
- Only one lexical corpus and one domain sample are used.
- The random control is synthetic.
- No adversarial-key analysis is included.
- The positional encoder is arbitrary precision rather than fixed-width.
- Timing is environment-dependent.
- Selector-level speed does not establish end-to-end application performance.
- Alpha parameterizes a discrete allocation family rather than a continuously varying representation.
- Dataset-specific optima should not be treated as universal rules.
- The experiments do not provide inferential evidence that the observed optima generalize to all English words, all domains, or other languages.

---

## 10. Reproducibility

The repository contains the implementation, tests, pinned dataset provenance, benchmark scripts, ratio experiment, objective-specific analysis, metadata, and CI configuration used to produce the reported results.

The recommended validation command is:

```bash
pytest -q
```

The benchmark and research workflows should be rerun when changing algorithm code, dataset sources, normalization, dependencies, or experimental configuration.

GitHub Actions publishes the machine-readable ratio-analysis results as workflow artifacts, including the objective-specific optima and Pareto frontier.

---

## 11. JOSS Submission Preparation

Before submission, the manuscript should be converted from this outline into the final JOSS paper format and should include:

- a concise Summary;
- a clear Statement of Need;
- a properly referenced State of the Field;
- Software Design;
- Research Impact;
- a complete References section;
- software citation metadata;
- a transparent description of reproducibility and testing.

The final submission should also disclose any generative-AI assistance according to the journal's current policy and should identify the human author responsible for the scientific claims, code, experiments, and final manuscript.

The current document is therefore a **manuscript preparation outline**, not yet the final JOSS submission.

---

## 12. Conclusion

HPSS provides a simple way to construct compact representations from the boundaries of textual keys, but the experiments do not support a universal claim of superiority.

The main empirical finding is more specific: **the preferred allocation of a fixed character budget between the beginning and end of a key depends on both the statistical structure of the key distribution and the objective being optimized**.

For the tested English corpus, balanced HPSS is not optimal at larger `k`, and increasingly prefix-heavy allocations perform better. For the tested ASCII domain sample, prefix-only selection is consistently best. For random ASCII strings, allocation matters little once enough characters are retained. The ratio experiment further shows that collision metrics and speed can favor different allocations.

These findings motivate treating HPSS as a representation heuristic whose parameters should be evaluated against the intended key distribution and objective, rather than as a universally optimal hashing construction.
