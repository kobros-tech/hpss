---
title: "HPSS: Hybrid Prefix-Suffix Selection for Compact Textual Key Representations"
authors:
  - name: Mohamed Alkobrosly
    affiliation: Independent Researcher
date: 17 August 2026
bibliography: paper.bib
---

# Summary

HPSS (Hybrid Prefix-Suffix Selection) is research software for constructing and evaluating compact textual-key representations. Given a character budget, it selects characters from the beginning and end of a key and can pass the resulting representation to an encoder or hash function. The software is designed for researchers and developers studying string representations, collision behavior, hashing, and reproducible empirical experiments.

A central feature is the separation of **representation collisions**—information loss caused by character selection—from collisions introduced by a downstream fixed-width hash. This distinction lets users evaluate the selection strategy independently of the particular hash function used afterward.

The repository provides the selector, positional encoder, reference hash-function implementations, shared dataset loading and normalization, collision-analysis utilities, reproducible benchmarks, automated tests, and continuous integration. The primary experimental scope is ASCII-oriented textual data.

# Statement of need

Compact textual representations are useful when an application or experiment needs deterministic keys with bounded size, including indexing, lookup structures, string-fingerprint studies, and preprocessing pipelines. Selecting a fixed number of characters is simple, but the information retained by a prefix, suffix, middle segment, or combination of boundary characters depends on the input distribution.

Existing hash libraries provide efficient mappings from complete byte or string sequences to fixed-width values, but they do not expose the information-loss behavior of a character-selection stage performed before hashing. Researchers who want to study that stage otherwise have to build their own selectors, collision accounting, dataset normalization, and reproducibility machinery.

HPSS addresses this gap as an **experimental research-software framework**, not as a replacement for established hash functions. Its target users are researchers and developers who need to compare positional selection strategies under a controlled, reproducible protocol.

# State of the field

FNV-1a [@fnv], MurmurHash3 [@murmurhash3], and xxHash [@xxhash] are established non-cryptographic hash implementations for compact fixed-width hashing. HPSS does not attempt to replace these libraries. Instead, it makes a preceding representation-selection step explicit and allows the same selected representation to be evaluated with multiple downstream hashes.

General-purpose hash libraries are appropriate when the complete input should be hashed. They do not, by design, provide an experimental framework for asking how much information is lost by retaining selected positions before hashing. HPSS therefore follows a **build rather than contribute** rationale: the scholarly software contribution is the integrated selector, collision taxonomy, exhaustive allocation analysis, shared data pipeline, reproducible benchmark protocol, and tests that make this specific research question directly reproducible.

The project also follows established software-citation practice [@joss] and provides citation metadata for reuse.

# Software design

For a key $x$, a budget $k$, and a front allocation $p$, HPSS studies the representation family

$$R(k,p,x)=x[:p] + x[-(k-p):], \qquad 0\leq p\leq k.$$ 

The balanced HPSS strategy is one member of this family, using $p=\lfloor k/2\rfloor$. Keeping the general allocation as a first-class experimental object prevents the implementation from assuming that the balanced split is optimal.

The software separates four stages: dataset normalization, character selection, representation-level collision analysis, and optional downstream hashing. This architecture is important because a collision introduced by selection cannot be repaired by a later hash function. The positional encoder uses an arbitrary-precision integer representation and is injective over finite selected strings; it is therefore treated as an encoding rather than as a fixed-width hash.

Research datasets are loaded through a shared canonical module so that benchmark programs use identical normalization and deduplication rules. External datasets are downloaded from pinned upstream sources, while the synthetic control uses a fixed random seed. Machine-readable benchmark outputs and metadata are retained for reproducibility.

The repository includes automated unit tests and GitHub Actions for both software validation and research-benchmark execution. The implementation is intentionally small and dependency-light: the reference hash functions are optional research baselines, while the core selection and encoding logic uses the Python standard library.

# Research impact statement

The software has been used by its author to conduct and reproduce the empirical study included with the repository. The project provides concrete research materials rather than only a conceptual proposal: a complete implementation, automated tests, continuous integration, pinned dataset provenance, deterministic controls, benchmark programs, and machine-readable result files are publicly available.

The resulting software is intended to make positional-allocation experiments repeatable and to provide a reusable starting point for researchers investigating compact textual representations. The repository's reproducibility infrastructure is therefore part of the research contribution; detailed experimental findings are documented separately in the repository's research materials rather than presented here as evidence that HPSS is a universally superior hashing method.

# AI usage disclosure

Generative AI was used during development with **OpenAI GPT-5.6 Luna** to assist with code review, refactoring, test scaffolding, debugging, benchmark-result analysis, and drafting and editing repository documentation and manuscript text. AI assistance was used across implementation, tests, research documentation, and this software paper; it did not replace the author's research decisions. The author reviewed, edited, and validated AI-assisted outputs, ran the software and tests, made the architectural and experimental decisions, and accepts responsibility for the accuracy, originality, licensing, and reproducibility of the submission.

# Acknowledgements

This work received no external financial support. No sponsor or funding body was involved in the design, implementation, analysis, or preparation of the software and manuscript.

# References

The references below identify the principal software, datasets, and software-citation guidance used by the project. The repository contains additional provenance metadata for benchmark inputs.
