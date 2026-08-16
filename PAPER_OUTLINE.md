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

## 2. Related Concepts
- Hash functions and fixed-width collision spaces.
- Feature/key selection and information loss.
- Distinction between representation collisions and hash collisions.

## 3. HPSS Method
- Formal selector definition.
- Even-k and odd-k rules.
- Short-key behavior.
- Positional encoding and its injectivity argument.
- Complexity and representation-length discussion.

## 4. Experimental Design
- Datasets and provenance.
- Normalization.
- Baselines: PREFIX, SUFFIX, MIDDLE.
- Encoders: HPSS positional encoder, FNV-1a, MurmurHash3, xxHash64.
- Metrics.
- Timing protocol and repetitions.

## 5. Results
- Representation uniqueness versus k.
- Collision-entry rate versus k.
- Collision pairs and maximum groups.
- Downstream hash collisions among distinct representations.
- Throughput.
- Odd-k results as a sensitivity/definition experiment.

## 6. Discussion
The central result should be framed as evidence about representation quality,
not as evidence that an arbitrary-precision positional integer is a better
64-bit hash function than established 64-bit hashes.

Discuss cases where MIDDLE has fewer collision pairs or smaller maximum groups,
even when HPSS has more unique representations. This prevents a single-metric
claim from overstating the evidence.

## 7. Limitations
- Finite datasets.
- Dictionary-specific structure.
- Normalization choices.
- No adversarial distribution analysis yet.
- Arbitrary-precision output is not a fixed-width hash.
- Timing results depend on hardware and runtime.

## 8. Reproducibility
Provide exact commands, dependency versions, Python version, dataset location,
benchmark configuration, and generated CSV metadata.

## 9. Conclusion
Answer the research questions narrowly and identify the next experiments needed
before making broader claims.
