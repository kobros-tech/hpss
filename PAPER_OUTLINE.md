# HPSS Research Paper Outline

## Title
**Hybrid Prefix-Suffix Selection for Compact Textual Key Representations: An Empirical Collision Study**

## Abstract
State the problem, define HPSS, describe the separation of representation and
hash collisions, identify the datasets and baselines, summarize the principal
results, and state limitations without claiming universal superiority.

## 1. Introduction
- Motivation: compact textual representations and hash-table workloads.
- Why selecting characters before hashing can dominate observed collisions.
- Research questions and contributions.
- Explicitly distinguish the selector contribution from the downstream encoder.

## 2. Related Concepts
- Hash functions and fixed-width collision spaces.
- Feature/key selection and information loss.
- Prefix/suffix and positional string representations.
- Distinction between representation collisions and hash collisions.

## 3. HPSS Method
- Formal selector definition.
- Even-k and odd-k rules.
- Short-key behavior.
- General front/back allocation family `R(k,p)`.
- Positional encoding and its injectivity argument.
- Complexity and representation-length discussion.

## 4. Experimental Design
- Datasets and provenance.
- Normalization.
- Baselines: PREFIX, SUFFIX, MIDDLE.
- Allocation ablation: every `p` from `0` to `k`.
- Controls: deterministic random strings and structured identifiers.
- Length-stratified analysis.
- Encoders: HPSS positional encoder, FNV-1a, MurmurHash3, xxHash64.
- Metrics: unique representations, collision entries, pairs, maximum group,
  and collision-group distribution.
- Timing protocol and repetitions.
- Paired bootstrap confidence intervals where sampling is appropriate.

## 5. Results
- Representation uniqueness versus k.
- Full front/back allocation heatmaps or tables.
- Whether the balanced split is actually optimal.
- Comparison across lexical, random, and structured controls.
- Collision-entry rate versus k.
- Collision pairs and collision-group distributions.
- Input-length effects.
- Downstream hash collisions among distinct representations.
- Throughput, clearly separated from representation quality.

## 6. Discussion
The central result should be framed as evidence about representation quality,
not as evidence that an arbitrary-precision positional integer is a better
64-bit hash function than established 64-bit hashes.

Discuss cases where MIDDLE has fewer collision pairs or smaller maximum groups,
even when HPSS has more unique representations. Explain whether any observed
advantage is specific to English lexical structure or persists on non-linguistic
controls.

The most important scientific question is whether boundary selection produces a
reproducible advantage and whether the advantage has an explainable relationship
to the distribution of the underlying keys.

## 7. Limitations
- Finite datasets.
- Dictionary-specific and language-specific structure.
- Synthetic controls are not substitutes for independent real-world datasets.
- Normalization choices.
- No universal adversarial guarantee.
- Arbitrary-precision output is not a fixed-width hash.
- Timing results depend on hardware and runtime.

## 8. Reproducibility
Provide exact commands, dependency versions, Python version, dataset location,
benchmark configuration, random seeds, and generated CSV metadata.

The repository's `research_benchmark.py` should be the canonical entry point for
the allocation, synthetic-control, and length-stratified experiments.

## 9. Conclusion
Answer the research questions narrowly. If the results do not show consistent
generalization, present HPSS as a dataset-dependent representation heuristic
rather than a universally superior method.
