---
title: "HPSS: Hybrid Prefix-Suffix Selection for Compact Textual Key Representations"
authors:
  - name: Mohamed Alkobrosly
    affiliation: Independent Researcher
date: 2026-08-17
bibliography: paper.bib
---

# Summary

HPSS (Hybrid Prefix-Suffix Selection) is a reproducible research software package for studying compact representations of textual keys. The software selects a fixed number of characters from the beginning and end of an input string and can subsequently encode or hash the resulting representation. The project asks a practical research question: when a textual key must be reduced to a fixed character budget, how should that budget be allocated between the front and back of the key?

The package provides the selector, positional encoder, established hash-function baselines, deterministic benchmark tooling, dataset provenance, collision analysis, and automated tests. A central design feature is the explicit separation of **representation collisions**—information loss caused by selection—from collisions introduced by a downstream hash function.

# Statement of Need

Compact textual representations are useful when applications need deterministic keys with bounded size, for example in indexing, lookup structures, experiments on string fingerprints, or preprocessing pipelines. A simple way to obtain such a representation is to retain a fixed number of characters from a string. However, choosing only a prefix, suffix, middle segment, or a combination of boundary characters can discard different information depending on the distribution of the keys.

HPSS provides a reproducible framework for investigating this selection problem rather than assuming that a particular allocation is universally optimal. It is intended for researchers and developers studying string representations, collision behavior, hashing, and reproducible empirical comparisons.

The software is deliberately not presented as a replacement for established fixed-width cryptographic or non-cryptographic hash functions. Its primary research object is the **representation-selection stage** before hashing.

# State of the Field

Prefix, suffix, substring, truncation, and fingerprinting techniques are common ways of constructing compact string-derived keys. Established non-cryptographic hash functions such as FNV-1a [@fnv], MurmurHash3 [@murmurhash3], and xxHash [@xxhash] provide efficient fixed-width mappings, but they do not recover information discarded before hashing. HPSS therefore complements rather than replaces such functions: the software makes the pre-hash representation an explicit experimental object and compares it with simple positional baselines.

The scholarly contribution of the package is the reproducible experimental framework around the allocation problem. It exhaustively evaluates every front/back allocation for a fixed character budget and reports representation-level collision statistics separately from downstream hashing. This makes it possible to test whether an apparent hashing improvement is actually caused by the selected representation.

# Software Design

For a key `x`, a budget `k`, and a front allocation `p`, the general representation family is

`R(k,p,x) = x[:p] + x[-(k-p):]`.

The implementation handles short inputs explicitly and provides the balanced HPSS strategy as a particular member of this family. The positional encoder maps the selected character sequence to an arbitrary-precision integer without deliberately introducing collisions between distinct selected sequences. Established hash functions can then be applied independently for comparison.

The benchmark architecture keeps dataset loading and normalization in a shared module so that the main benchmark and allocation experiments use the same records. Research datasets are obtained from pinned upstream sources rather than silently changing copies. The English-word source is derived from the `dwyl/english-words` repository [@dwylEnglishWords], while the domain control is derived from the Estonian Internet Foundation domain dataset [@estonianDomains]. Deterministic synthetic controls use a fixed seed.

The repository includes automated unit tests and GitHub Actions workflows for validation and benchmark execution. Research outputs are written as machine-readable CSV files and benchmark metadata records the relevant dataset and execution information.

# Research Impact

The software provides a reproducible reference implementation and benchmark suite for the allocation question studied in this work. The experiments use a large English-word dataset, a real-world ASCII domain dataset, and deterministic random ASCII controls. Across these datasets, the optimal front/back allocation is not universal: English words show a strong asymmetric preference at larger budgets, domains favor prefix-only selection, and random strings become largely insensitive to allocation once enough characters are retained.

These results provide credible near-term research value because the repository exposes the complete experimental procedure, test suite, dataset provenance, and machine-readable outputs needed to reproduce and extend the analysis.

# AI Usage Disclosure

Generative AI tools were used during development to assist with code review, refactoring, test scaffolding, benchmark analysis, and drafting/editing documentation and manuscript text. The author reviewed and validated the resulting code and text, made the research and architectural decisions, and is responsible for the accuracy, originality, licensing, and reproducibility of the submission.

# References

The references below identify the principal software and datasets used by the package and article. The repository also contains detailed provenance information for benchmark inputs.
