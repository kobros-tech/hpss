# HPSS Real-World Hashing Research Report

## HPSS vs. Established 64-bit Hash Functions on `dwyl/english-word`

**Dataset:** `dwyl/english-word` — `words.txt`  
**Records benchmarked:** 466,550  
**Selection lengths:** `k ∈ {2, 4, 6, 8, 10, 12}`  
**Selection strategies:** `PREFIX`, `SUFFIX`, `HPSS`, `MIDDLE`  
**Hash functions:** HPSS positional encoding, FNV-1a 64-bit, MurmurHash3 64-bit, xxHash64

---

## 1. Executive Summary

This study evaluates the proposed **HPSS positional hashing approach** against established 64-bit hash functions using a substantially larger and more realistic English-word corpus than the earlier CS50 dictionary experiment.

The most important methodological point is that this experiment separates two fundamentally different phenomena:

1. **Representation collisions** — two different words are mapped to the same selected character representation before hashing.
2. **Hash collisions** — two distinct representations are mapped to the same final hash value.

This distinction is essential.

The current results show that, for every tested `k` and selection strategy, the reported collision statistics for `HPSS_POSITIONAL`, FNV-1a, MurmurHash3, and xxHash64 are **identical**.

That is not evidence that all four hash functions have identical collision behavior in general. Rather, it is a direct consequence of the benchmark design and the observed dataset:

> The dominant collisions are created by the character-selection stage, not by the 64-bit hash stage.

For example, with `k = 12` and the HPSS selection strategy:

- 462,335 unique representations are produced from 466,550 words.
- 4,215 input entries are therefore involved in representation duplication.
- The representation collision-entry rate is only **0.9034%**.
- All four tested hash functions preserve exactly the same 462,335 unique values in this experiment.
- Therefore no additional hash collisions are observed among the distinct selected representations.

This is an important positive result for HPSS's positional encoder, but it must be interpreted correctly: the experiment demonstrates **collision-free behavior on this finite set of selected representations**, not a universal proof that a fixed-width hash function cannot collide.

The strongest result is therefore not "HPSS beats xxHash at collision resistance." It is:

> **HPSS's selection strategy can retain substantially more information than simple prefix/suffix selection at small and medium `k`, while its positional encoding does not introduce additional collisions in the tested dataset.**

At `k = 10`, for example:

| Strategy | Unique representations | Collision-entry rate | Collision pairs | Max group |
|---|---:|---:|---:|---:|
| PREFIX | 407,315 | 12.6964% | 133,334 | 31 |
| SUFFIX | 413,765 | 11.3139% | 251,730 | 199 |
| **HPSS** | **445,300** | **4.5547%** | **76,200** | **147** |
| MIDDLE | 439,498 | 5.7983% | 43,317 | 27 |

Thus HPSS is markedly better than PREFIX and SUFFIX in representation uniqueness at this setting, while MIDDLE produces fewer collision pairs and a smaller maximum group despite having fewer unique representations.

This means the research question is now more interesting than a simple "which hash function has fewer collisions?" comparison. The central issue is becoming:

> **How effectively does HPSS select a compact representation of a real-world key while preserving distinguishability, and what computational cost does that representation provide?**

---

# 2. Research Objective

The objective of this experiment is to determine whether HPSS provides a meaningful hashing/representation mechanism for real-world textual keys.

The investigation focuses on four questions:

### Q1. Representation quality

How many distinct textual keys remain distinguishable after HPSS selects only `k` characters?

### Q2. Selection-strategy quality

Does HPSS preserve more distinct representations than simpler strategies such as:

- PREFIX
- SUFFIX
- MIDDLE

### Q3. Hash-stage behavior

After the selected representation is generated, does HPSS's positional encoding introduce additional collisions?

### Q4. Performance

How does the computational throughput of HPSS compare with established 64-bit hash functions?

---

# 3. Dataset

The benchmark uses:

**`dwyl/english-word`**

specifically:

```text
words.txt
```

The dataset contains:

```text
466,550
```

records in the supplied benchmark run.

This is considerably larger than the earlier 143,091-entry CS50 "large" dictionary experiment.

The larger corpus is useful because collision behavior depends heavily on the structure and diversity of the input population.

A method that looks good on a small dictionary may behave differently when exposed to hundreds of thousands of real-world lexical entries.

---

# 4. Data Normalization

The benchmark loads the dictionary using:

```python
line.strip().lower()
```

Therefore the experiment:

1. removes surrounding whitespace;
2. ignores empty lines;
3. converts every key to lowercase.

This means the experiment evaluates the normalized textual key space rather than preserving case distinctions.

This choice should be explicitly documented in any future paper because it affects reproducibility.

---

# 5. Experimental Variables

The experiment varies three principal dimensions.

## 5.1 Selection length

The number of selected characters is:

\[
k \in \{2,4,6,8,10,12\}
\]

Increasing `k` gives the selection strategy more information with which to distinguish words.

---

## 5.2 Selection strategy

Four strategies are evaluated:

### PREFIX

Selects characters from the beginning of the word.

Conceptually:

\[
R_{\text{prefix}}(w,k)
=
w_0w_1\ldots w_{k-1}
\]

### SUFFIX

Selects characters from the end:

\[
R_{\text{suffix}}(w,k)
=
w_{|w|-k}\ldots w_{|w|-1}
\]

### MIDDLE

Selects a middle region according to the implementation.

### HPSS

Uses the proposed HPSS character-selection mechanism.

The exact mathematical definition of HPSS should be included in the final paper as a formal algorithm specification. This README deliberately does not invent a definition that is not present in the supplied benchmark source.

---

# 6. The Crucial Experimental Separation

The benchmark correctly distinguishes:

```text
word
  │
  ▼
selection strategy
  │
  ▼
selected representation
  │
  ├── representation collisions
  │
  ▼
hash / positional encoder
  │
  ▼
final hash value
  │
  └── hash collisions
```

This separation is the foundation of the experiment.

Suppose:

```text
word A → "abcdef"
word B → "abcdef"
```

These two words have already become indistinguishable.

No hash function can recover the information that was discarded by the selection strategy.

Therefore:

\[
R(A)=R(B)
\]

is a **representation collision**, not evidence of poor behavior by FNV-1a, MurmurHash3, xxHash64, or HPSS's positional encoder.

---

# 7. Collision Metrics

For a set of `n` inputs, let the number of distinct values be:

\[
U
\]

The benchmark defines:

\[
C_{\text{entries}} = n-U
\]

as the number of collision entries.

The corresponding collision-entry rate is:

\[
\rho =
\frac{n-U}{n}
\]

or, as a percentage:

\[
\rho_{\%}
=
100
\frac{n-U}{n}
\]

---

## 7.1 Collision pairs

If a value occurs `f` times, it contributes:

\[
\binom{f}{2}
=
\frac{f(f-1)}{2}
\]

colliding pairs.

Therefore:

\[
C_{\text{pairs}}
=
\sum_i
\binom{f_i}{2}
\]

where `f_i` is the frequency of representation/hash value `i`.

This metric is important because two systems can have the same number of collision entries but very different concentration of collisions.

---

## 7.2 Maximum collision group

The benchmark also reports:

\[
C_{\max} = \max_i f_i
\]

This identifies the largest group of input entries sharing one representation or hash value.

A large maximum group can be particularly important for lookup systems, indexing, bucket distributions, and compact key schemes.

---

# 8. Main Results

## 8.1 Complete representation results

The following table summarizes the unique representations and collision-entry rates.

| k | PREFIX unique | PREFIX rate | SUFFIX unique | SUFFIX rate | HPSS unique | HPSS rate | MIDDLE unique | MIDDLE rate |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 828 | 99.8225% | 817 | 99.8249% | 837 | 99.8206% | 898 | 99.8075% |
| 4 | 38,694 | 91.7064% | 38,412 | 91.7668% | 46,895 | 89.9486% | 64,759 | 86.1196% |
| 6 | 184,988 | 60.3498% | 189,260 | 59.4341% | 250,828 | 46.2377% | 279,479 | 40.0967% |
| 8 | 325,545 | 30.2229% | 333,801 | 28.4533% | 392,351 | 15.9038% | 389,992 | 16.4094% |
| 10 | 407,315 | 12.6964% | 413,765 | 11.3139% | 445,300 | 4.5547% | 439,498 | 5.7983% |
| 12 | 445,322 | 4.5500% | 449,753 | 3.6003% | 462,335 | 0.9034% | 458,578 | 1.7087% |

### Interpretation

HPSS substantially outperforms PREFIX and SUFFIX in unique representation count from `k = 4` onward.

At `k = 8`:

\[
392,351
\]

unique HPSS representations are obtained, compared with:

\[
325,545
\]

for PREFIX.

At `k = 10`:

\[
445,300
\]

HPSS representations are unique, corresponding to only:

\[
4.5547\%
\]

collision entries.

At `k = 12`:

\[
462,335
\]

of 466,550 entries remain unique.

That corresponds to:

\[
\frac{462335}{466550}
\approx 99.0966\%
\]

unique input representations.

This is the strongest representation result in the supplied benchmark.

---

# 9. HPSS Compared with PREFIX and SUFFIX

The most important practical comparison is against simple selection strategies.

## k = 6

| Strategy | Unique | Collision entries | Collision pairs | Max group |
|---|---:|---:|---:|---:|
| PREFIX | 184,988 | 281,562 | 4,935,894 | 1,027 |
| SUFFIX | 189,260 | 277,290 | 18,244,102 | 2,694 |
| **HPSS** | **250,828** | **215,722** | **3,999,078** | **592** |
| MIDDLE | 279,479 | 187,071 | 759,469 | 152 |

HPSS produces:

\[
250,828
\]

unique representations versus:

\[
184,988
\]

for PREFIX.

The relative increase in unique representations is approximately:

\[
\frac{250828-184988}{184988}
\approx 35.59\%
\]

Thus HPSS provides a substantial improvement over PREFIX at `k = 6`.

However, MIDDLE produces even more unique representations at this particular `k`.

This is important scientifically: the results do **not** justify claiming that HPSS universally dominates every selection strategy.

---

# 10. HPSS at k = 8

At `k = 8`:

| Strategy | Unique | Collision entries | Collision pairs | Max group |
|---|---:|---:|---:|---:|
| PREFIX | 325,545 | 141,005 | 546,516 | 139 |
| SUFFIX | 333,801 | 132,749 | 2,527,296 | 952 |
| **HPSS** | **392,351** | **74,199** | **498,441** | **355** |
| MIDDLE | 389,992 | 76,558 | 167,865 | 54 |

HPSS now exceeds both PREFIX and SUFFIX in unique representations.

It also slightly exceeds MIDDLE in unique representations:

\[
392,351 > 389,992
\]

However, MIDDLE has considerably fewer collision pairs and a much smaller maximum collision group.

This reveals an important distinction:

> **Unique-count performance and collision-concentration performance are not the same objective.**

---

# 11. HPSS at k = 10

At `k = 10`:

| Strategy | Unique | Collision entries | Collision pairs | Max group |
|---|---:|---:|---:|---:|
| PREFIX | 407,315 | 59,235 | 133,334 | 31 |
| SUFFIX | 413,765 | 52,785 | 251,730 | 199 |
| **HPSS** | **445,300** | **21,250** | **76,200** | **147** |
| MIDDLE | 439,498 | 27,052 | 43,317 | 27 |

HPSS has the highest unique representation count.

Its collision-entry count is:

\[
21,250
\]

which is lower than PREFIX, SUFFIX, and MIDDLE.

This is a particularly strong operating point for HPSS.

However, MIDDLE still produces fewer collision pairs:

\[
43,317 < 76,200
\]

and a smaller maximum collision group:

\[
27 < 147
\]

Therefore, if the application's objective is specifically to minimize pairwise collision concentration rather than maximize unique representations, MIDDLE deserves serious consideration.

---

# 12. HPSS at k = 12

At `k = 12`, the difference becomes especially strong.

| Strategy | Unique | Collision entries | Collision pairs | Max group |
|---|---:|---:|---:|---:|
| PREFIX | 445,322 | 21,228 | 37,659 | 28 |
| SUFFIX | 449,753 | 16,797 | 43,366 | 111 |
| **HPSS** | **462,335** | **4,215** | **9,714** | **63** |
| MIDDLE | 458,578 | 7,972 | 10,406 | 12 |

HPSS has:

- the highest number of unique representations;
- the fewest collision entries;
- the fewest collision pairs;
- but not the smallest maximum collision group.

Its collision-entry rate is only:

\[
0.90344\%
\]

This means approximately:

\[
99.10\%
\]

of the 466,550 input entries have unique HPSS representations at `k = 12`.

---

# 13. Collision Scaling with k

A major pattern emerges:

| k | HPSS collision-entry rate |
|---:|---:|
| 2 | 99.8206% |
| 4 | 89.9486% |
| 6 | 46.2377% |
| 8 | 15.9038% |
| 10 | 4.5547% |
| 12 | 0.9034% |

The decrease is strongly nonlinear.

The selection space becomes dramatically more discriminative as `k` increases.

The transition between `k = 6` and `k = 10` is especially important:

\[
46.24\%
\rightarrow
4.55\%
\]

This is approximately a tenfold reduction in collision-entry rate.

From `k = 10` to `k = 12`:

\[
4.5547\%
\rightarrow
0.9034\%
\]

which is approximately a fivefold reduction.

This suggests that HPSS may have useful operating points where a relatively small selected representation retains most of the distinctiveness of the original key.

---

# 14. Hash-Stage Results

The most striking feature of the CSV is that the hash statistics are identical for:

- HPSS_POSITIONAL
- FNV1A64
- MURMUR3_64
- XXHASH64

for every tested `k` and selection strategy.

For example, at:

```text
k = 12
strategy = HPSS
```

all four produce:

```text
unique = 462,335
collision entries = 4,215
collision rate = 0.0090344
collision pairs = 9,714
max group = 63
```

This should be interpreted carefully.

The four algorithms are **not being shown to be mathematically equivalent hash functions**.

Instead, the experiment demonstrates that, for the finite set of selected representations generated from this dataset:

\[
\text{distinct representations}
\rightarrow
\text{distinct observed outputs}
\]

for all four tested implementations.

Therefore:

\[
C_{\text{hash-stage}} = 0
\]

for the distinct representations observed in this benchmark.

The remaining collisions are inherited from the selection stage.

---

# 15. Why the Hash Statistics Are Identical

Suppose the selection stage produces:

\[
U_R
\]

unique representations.

If the hash function maps all `U_R` representations to distinct output values, then:

\[
U_H = U_R
\]

and:

\[
C_H = n-U_H = n-U_R = C_R
\]

where:

- `U_R` = unique representations;
- `U_H` = unique hash outputs;
- `C_R` = representation collision entries;
- `C_H` = hash collision entries.

This is exactly what the supplied results show.

Thus the benchmark indicates that the selection strategy is the dominant source of observed collisions.

---

# 16. Important Limitation: 64-bit Hashes Are Not Injective

It is essential not to conclude:

> "FNV-1a, MurmurHash3, and xxHash64 are collision-free."

That statement would be mathematically incorrect.

A 64-bit hash has at most:

\[
2^{64}
\]

possible outputs.

The set of arbitrary strings is vastly larger than:

\[
2^{64}
\]

Therefore no fixed-width 64-bit hash can be globally injective over all possible strings.

The correct conclusion is:

> **No additional collisions were observed among the tested distinct representations in this finite benchmark.**

This distinction is critical for publication-quality scientific writing.

---

# 17. HPSS Positional Encoding

The benchmark describes HPSS positional encoding as a Unicode code-point-based encoder:

\[
d(c)=\operatorname{ord}(c)+1
\]

The purpose is to encode selected characters while preserving positional information.

Conceptually, for a representation:

\[
r=c_1c_2\ldots c_k
\]

the encoder incorporates both:

1. the identity of each character;
2. its position within the representation.

This is fundamentally different from simply treating the selected characters as an unordered set.

For a fixed representation length and a sufficiently wide mathematical integer representation, positional encoding can be injective over the supported symbol alphabet.

However, if the implementation ultimately restricts the result to a finite fixed-width machine integer, the global injectivity claim must be qualified by the available output space.

The paper should therefore distinguish:

### Mathematical positional representation

Potentially injective under explicit domain/width assumptions.

### Fixed-width machine encoding

Subject to the finite range of the chosen integer type.

This distinction should be made explicit in the final formal specification.

---

# 18. Performance Results

The benchmark also measures hashes per second.

The results show a consistent performance hierarchy.

At most tested configurations:

```text
XXHASH64
    >
MURMUR3_64
    >
HPSS_POSITIONAL
    >
FNV1A64
```

although exact rankings vary slightly by selection length and workload.

For example, at:

```text
k = 12
strategy = HPSS
```

the measured throughputs are approximately:

| Hash | Hashes/sec |
|---|---:|
| HPSS_POSITIONAL | 1.024 million/s |
| FNV1A64 | 0.889 million/s |
| MurmurHash3 | 3.421 million/s |
| xxHash64 | 3.821 million/s |

Therefore HPSS is substantially slower than MurmurHash3 and xxHash64 in this Python benchmark.

At the same time, HPSS is faster than FNV-1a in this particular implementation.

---

# 19. Performance Interpretation

The performance result is important because collision behavior alone does not determine whether a hashing scheme is practically useful.

For a production hash table or indexing system, relevant objectives may include:

\[
\text{quality}
+
\text{speed}
+
\text{memory efficiency}
+
\text{implementation complexity}
\]

The current data suggests:

### xxHash64

Strongest measured throughput.

### MurmurHash3

Also substantially faster than HPSS in this benchmark.

### HPSS

Moderate throughput, with a different design objective centered around structured positional representation.

### FNV-1a

Lowest or near-lowest throughput among the tested reference functions in this Python implementation.

The important caveat is that these timings measure the **specific implementations and Python call paths**, not the intrinsic machine-code performance of the underlying algorithms.

A publication should therefore avoid statements such as:

> "HPSS is inherently slower than xxHash."

Instead:

> "In the supplied Python benchmark implementation, xxHash64 and MurmurHash3 achieved substantially higher measured throughput than HPSS_POSITIONAL."

---

# 20. The Benchmark Is Not a Pure Hash-Function Benchmark

This is perhaps the most important conceptual point.

The benchmark actually evaluates a pipeline:

\[
\boxed{
\text{word}
\rightarrow
\text{selection}
\rightarrow
\text{representation}
\rightarrow
\text{hash}
}
\]

Therefore it is better described as a:

> **compact textual representation and hashing benchmark**

rather than a pure universal hash-function benchmark.

The selection strategy is responsible for most of the observed collisions.

Consequently, comparing only the final collision rate without separating the two stages would obscure the most interesting property of HPSS.

---

# 21. Scientific Strength of the Current Experiment

The experiment has several strong methodological properties.

## 21.1 Same input corpus

Every strategy is evaluated on exactly the same:

\[
466,550
\]

entries.

## 21.2 Same selected representations

Reference hash functions are applied to the same representations generated by each strategy.

This is crucial.

It means differences in the final hash statistics cannot be attributed to one hash function receiving a different representation.

## 21.3 Collision decomposition

The benchmark separately reports:

- representation uniqueness;
- representation collisions;
- representation collision pairs;
- representation maximum group;
- final hash uniqueness;
- final hash collisions;
- final hash collision pairs;
- final hash maximum group.

This makes the experiment much more informative than a single collision percentage.

## 21.4 Median timing

Five timing repetitions are used, and the median is reported.

This reduces the influence of occasional scheduling noise.

## 21.5 UTF-8 preservation

The benchmark explicitly uses:

```python
representation.encode("utf-8")
```

rather than ASCII with ignored characters.

That is an important correction because silently discarding unsupported characters would alter the selected representation and could artificially create collisions.

---

# 22. Scientific Weaknesses and Limitations

The experiment is strong as a first real-world benchmark, but it is not yet sufficient by itself for a research paper claiming a new general-purpose hash function.

## 22.1 One corpus

Only one primary corpus is currently evaluated.

The `dwyl/english-word` dataset is useful, but it represents one domain:

> English lexical strings.

A stronger study should include heterogeneous datasets.

Recommended categories:

- English words;
- URLs;
- usernames;
- filenames;
- software package names;
- random strings;
- natural-language tokens;
- mixed alphanumeric identifiers;
- Unicode text.

---

## 22.2 Selection bias

A selection strategy can perform extremely well on one corpus and poorly on another.

This is particularly relevant to HPSS because its purpose is to select informative characters.

The experiment therefore needs adversarial and non-English inputs before general claims are made.

---

## 22.3 Fixed k values

Only:

\[
k=2,4,6,8,10,12
\]

are evaluated.

A broader sweep could reveal the complete collision curve.

For example:

\[
k=1,2,\ldots,20
\]

or until every dataset entry becomes unique.

---

## 22.4 No memory-size analysis

The benchmark measures collision behavior and throughput, but does not yet evaluate:

- output width;
- memory consumed by the representation;
- dictionary/table size;
- cache behavior;
- bucket distribution;
- lookup latency.

These should be investigated if HPSS is intended for a practical indexing system.

---

## 22.5 No adversarial analysis

A serious hashing paper should investigate whether an attacker can deliberately construct many inputs that produce the same selected representation.

For example:

\[
R(w_1)=R(w_2)=\cdots=R(w_m)
\]

Such behavior could produce severe bucket concentration.

This is especially important if HPSS is ever proposed for hash tables exposed to untrusted input.

---

## 22.6 No statistical significance analysis

The current dataset is large enough for descriptive conclusions, but the study does not yet report confidence intervals or statistical tests.

Timing experiments in particular should eventually report:

- median;
- mean;
- standard deviation;
- interquartile range;
- confidence interval.

---

# 23. What the Current Results Actually Demonstrate

The strongest defensible conclusions are:

### Finding 1

HPSS produces substantially more unique selected representations than PREFIX and SUFFIX for `k ≥ 4` in this corpus.

### Finding 2

At `k = 8`, HPSS slightly exceeds MIDDLE in unique representations.

### Finding 3

At `k = 10`, HPSS produces the highest number of unique representations among the four tested strategies.

### Finding 4

At `k = 12`, HPSS produces:

\[
462,335
\]

unique representations from:

\[
466,550
\]

entries.

### Finding 5

At `k = 12`, HPSS's representation collision-entry rate is only:

\[
0.9034\%
\]

### Finding 6

No additional collisions were observed after applying any of the tested 64-bit hash functions to the distinct representations generated in this benchmark.

### Finding 7

xxHash64 and MurmurHash3 are substantially faster than the current Python implementation of HPSS positional encoding.

### Finding 8

The current results support HPSS as an interesting **compact representation/selection strategy**, but do not yet establish it as a superior general-purpose cryptographic or non-cryptographic hash function.

---

# 24. What the Results Do NOT Demonstrate

The experiment does **not** prove:

- that HPSS is collision-free;
- that HPSS is better than xxHash64 as a general-purpose hash;
- that HPSS is faster than established optimized hashes;
- that HPSS is cryptographically secure;
- that HPSS is resistant to adversarial collision attacks;
- that HPSS generalizes to arbitrary strings;
- that HPSS dominates MIDDLE under every collision metric.

These claims require separate experiments.

This distinction will be important if the work is developed into a peer-reviewed paper.

---

# 25. A Better Research Framing

The most promising scientific framing is probably not:

> "HPSS is a better hash function than xxHash."

The current evidence does not support that claim.

A stronger and more defensible framing is:

> **HPSS is a compact, structure-aware character-selection and positional encoding scheme that attempts to preserve key distinguishability while reducing representation size.**

Under this framing, conventional hash functions become downstream baselines.

The research question becomes:

\[
\boxed{
\text{How much information can HPSS preserve using only } k
\text{ selected characters?}
}
\]

That is a much more interesting question.

---

# 26. Information-Preservation Perspective

Suppose a dataset contains:

\[
N=466,550
\]

entries.

The theoretical minimum number of bits required to identify every entry uniquely is approximately:

\[
\log_2(N)
\]

For this dataset:

\[
\log_2(466550) \approx 18.83
\]

bits.

The selected representation therefore does not necessarily need to preserve the full original word.

It only needs to preserve enough information to distinguish the target population.

This leads to a useful research concept:

> **Dataset-relative distinguishability.**

A representation may be highly compressed while still being sufficiently unique for a particular population.

---

# 27. Representation Efficiency

A useful future metric is:

\[
E(k)
=
\frac{U(k)}{N}
\]

where:

- `U(k)` is the number of unique representations;
- `N` is the number of input entries.

For HPSS:

### k = 8

\[
E(8)
=
\frac{392351}{466550}
\approx 84.10\%
\]

### k = 10

\[
E(10)
=
\frac{445300}{466550}
\approx 95.45\%
\]

### k = 12

\[
E(12)
=
\frac{462335}{466550}
\approx 99.10\%
\]

This provides a much more intuitive way to describe the behavior.

---

# 28. HPSS Operating Points

The results suggest several possible operating points.

## Compact mode

`k = 6`

HPSS:

\[
250,828
\]

unique representations.

This is a significant improvement over PREFIX and SUFFIX but still has substantial collisions.

## Balanced mode

`k = 8`

HPSS:

\[
392,351
\]

unique representations.

This gives approximately:

\[
84.1\%
\]

unique representation coverage.

## High-distinguishability mode

`k = 10`

HPSS:

\[
445,300
\]

unique representations.

Approximately:

\[
95.45\%
\]

of the input entries have unique representations.

## Near-unique mode

`k = 12`

HPSS:

\[
462,335
\]

unique representations.

Approximately:

\[
99.10\%
\]

of the dataset is represented uniquely.

---

# 29. Comparison With Simple Strategies

The experiment reveals an important pattern.

At small `k`, simple prefix/suffix extraction throws away too much information.

HPSS is designed to select characters more intelligently, and this becomes increasingly valuable as `k` increases.

For example, at `k = 10`:

\[
U_{\text{HPSS}}=445300
\]

versus:

\[
U_{\text{PREFIX}}=407315
\]

The difference is:

\[
37,985
\]

additional unique representations.

Compared with SUFFIX:

\[
445300-413765
=
31,535
\]

additional unique representations.

Compared with MIDDLE:

\[
445300-439498
=
5,802
\]

additional unique representations.

Thus HPSS's strongest advantage in this dataset is against simple PREFIX and SUFFIX selection.

Its advantage over MIDDLE is much smaller.

---

# 30. Collision-Pair Analysis

Collision pairs tell a different story.

At `k = 10`:

```text
PREFIX   = 133,334
SUFFIX   = 251,730
HPSS      = 76,200
MIDDLE    = 43,317
```

Thus HPSS reduces pairwise collisions substantially relative to PREFIX and SUFFIX.

But MIDDLE remains better by this metric.

This suggests that a single scalar "collision score" may be inadequate.

A future paper should report at least:

\[
(U,\ C_{\text{entries}},\ C_{\text{pairs}},\ C_{\max})
\]

together.

---

# 31. Collision Concentration

The maximum collision group also reveals structural differences.

At `k = 6`:

```text
PREFIX   1,027
SUFFIX   2,694
HPSS       592
MIDDLE     152
```

HPSS substantially reduces the largest collision group compared with PREFIX and SUFFIX.

At `k = 12`:

```text
PREFIX      28
SUFFIX     111
HPSS        63
MIDDLE      12
```

Again, HPSS improves strongly over SUFFIX and is better than SUFFIX/PREFIX in several respects, but MIDDLE has the smallest maximum group.

Therefore HPSS should not be described as universally optimal.

---

# 32. Benchmark Architecture

The supplied benchmark has a clean architecture:

```text
load_words()
      │
      ▼
for k
      │
      ▼
for selection strategy
      │
      ├── generate representations
      │
      ├── measure representation collisions
      │
      ├── HPSS positional encoding
      │
      └── reference hashes
                │
                ├── FNV1A64
                ├── MURMUR3_64
                └── XXHASH64
```

This design ensures that every reference hash receives the same UTF-8 byte representation for a given selection strategy.

That is a strong aspect of the methodology.

---

# 33. Reproducibility

The benchmark is run with:

```bash
python3.11 benchmark.py
```

and produces:

```text
RESULTS_fresh.csv
```

The dataset path is:

```text
dictionaries/words.txt
```

The experiment configuration is:

```python
K_VALUES = [2, 4, 6, 8, 10, 12]
REPETITIONS = 5
```

The benchmark uses:

```python
statistics.median()
```

for timing.

For a research release, the following should also be recorded:

- Python version;
- operating system;
- CPU model;
- CPU frequency/governor if relevant;
- RAM;
- compiler version;
- library versions;
- exact Git commit;
- dataset commit/hash.

---

# 34. Recommended Next Experiments

The current benchmark is a strong Stage-4-style real-world evaluation, but the following experiments would substantially strengthen the research.

## Experiment A — Full k curve

Evaluate:

```text
k = 1 ... 20
```

and plot:

\[
k \rightarrow U(k)
\]

and:

\[
k \rightarrow \rho(k)
\]

for every selection strategy.

---

## Experiment B — Multiple datasets

Recommended datasets:

1. `dwyl/english-word`
2. CS50 large dictionary
3. URLs
4. usernames
5. filenames
6. package names
7. random ASCII strings
8. random Unicode strings
9. alphanumeric identifiers
10. natural-language corpora

This would determine whether HPSS is exploiting English orthographic structure or whether the effect generalizes.

---

# 35. Experiment C — Random Baseline

Introduce a random selection strategy.

For each word:

\[
R_{\text{random}}(w,k)
\]

select `k` positions using a reproducible random seed.

This provides an important baseline:

> Is HPSS actually selecting informative positions better than chance?

---

# 36. Experiment D — Adversarial Inputs

Construct inputs deliberately designed to collide under each strategy.

For example, for PREFIX:

```text
abcdefghXXXX
abcdefghYYYY
abcdefghZZZZ
```

All share the same prefix.

For SUFFIX:

```text
XXXXabcdefgh
YYYYabcdefgh
ZZZZabcdefgh
```

all share the same suffix.

The equivalent adversarial construction should be attempted against HPSS.

This experiment is essential for understanding whether HPSS's advantage survives intentional attacks.

---

# 37. Experiment E — Hash Distribution

Collision counts alone are not enough.

Measure the distribution of hash outputs across buckets.

For `B` buckets, measure:

\[
\chi^2
=
\sum_{i=1}^{B}
\frac{(O_i-E_i)^2}{E_i}
\]

where:

- `O_i` = observed bucket count;
- `E_i` = expected bucket count.

Also measure:

- variance;
- standard deviation;
- maximum bucket load;
- load-factor sensitivity;
- entropy.

This would test whether HPSS produces well-distributed hash-table buckets.

---

# 38. Experiment F — Avalanche Testing

If HPSS is intended to be called a hash function, perform avalanche tests.

Given:

\[
x
\]

and a one-bit modification:

\[
x'
\]

measure the Hamming distance:

\[
d_H(H(x),H(x'))
\]

For an ideal 64-bit avalanche behavior, the expected changed-bit count is approximately:

\[
32
\]

bits.

This should be measured over a large sample.

---

# 39. Experiment G — Bit Independence

Measure whether output bits behave independently.

For every output bit:

- calculate probability of `1`;
- calculate pairwise bit correlations;
- calculate conditional dependencies.

This would help determine whether HPSS's positional encoder behaves like a hash function or primarily like an injective encoding.

---

# 40. Experiment H — Performance in Native Code

The current Python timing should not be treated as the final performance result.

A stronger benchmark should implement HPSS and the reference algorithms under equivalent conditions in:

- C;
- C++;
- Rust;
- or optimized native extensions.

Measure:

\[
\text{keys/sec}
\]

and:

\[
\text{cycles/key}
\]

if possible.

This will make performance comparisons much more meaningful.

---

# 41. Experiment I — Memory Footprint

If HPSS is intended as a compact representation, measure:

- bytes per key;
- output width;
- memory used by an index;
- cache locality;
- lookup performance.

A method that is slightly slower but dramatically reduces memory could still be valuable.

---

# 42. Experiment J — Exact Collision Recovery

For every collision group, record examples:

```text
representation
word 1
word 2
...
```

This enables qualitative analysis of *why* collisions happen.

For example, collisions may arise from:

- morphological variants;
- prefixes;
- suffixes;
- plural forms;
- inflections;
- related words;
- short words;
- repeated patterns.

Understanding the collision structure could lead directly to an improved HPSS algorithm.

---

# 43. Research Hypothesis

A useful formal hypothesis for the paper would be:

### H1

For a fixed `k`, HPSS produces a higher number of unique representations than simple PREFIX and SUFFIX selection on structured lexical datasets.

### H2

HPSS produces lower representation collision rates as `k` increases.

### H3

The HPSS positional encoding introduces no additional observed collisions among the distinct representations in the tested corpus.

### H4

The current HPSS implementation has lower throughput than optimized modern non-cryptographic hashes such as xxHash64 and MurmurHash3.

### H5

HPSS's advantage is dataset-dependent and should therefore be evaluated across multiple classes of strings.

These hypotheses are testable and do not overclaim.

---

# 44. Current Evidence for the Hypotheses

| Hypothesis | Current evidence |
|---|---|
| H1 | **Supported** against PREFIX/SUFFIX on this corpus |
| H2 | **Supported** |
| H3 | **Supported observationally** on this dataset |
| H4 | **Supported** in the supplied Python benchmark |
| H5 | **Not yet tested sufficiently** |

This is a healthy research position: several hypotheses have strong preliminary support, while others remain open.

---

# 45. Main Research Contribution So Far

Based on the supplied experiment, the potentially publishable contribution is not yet a claim that HPSS is the world's best hash function.

The more promising contribution is:

> **A structure-aware compact character-selection strategy can preserve a high fraction of key distinguishability with substantially fewer selected characters than naive prefix/suffix extraction, while a positional encoding can preserve the selected representation without introducing additional observed collisions in a large real-world English-word corpus.**

The `dwyl/english-word` results provide meaningful evidence for this claim.

---

# 46. Strongest Numerical Result

The single result worth highlighting is:

\[
\boxed{
k=12,\quad
U_{\text{HPSS}}=462,335,\quad
N=466,550
}
\]

Therefore:

\[
\boxed{
E_{\text{HPSS}} \approx 99.10\%
}
\]

with only:

\[
\boxed{
4,215
}
\]

collision entries.

The collision-pair count is:

\[
\boxed{
9,714
}
\]

and the largest collision group contains:

\[
\boxed{
63
}
\]

entries.

These numbers demonstrate that the HPSS selection mechanism can represent almost the entire dictionary distinctly using only the selected `k=12` character representation.

---

# 47. Important Counterpoint

MIDDLE performs surprisingly well.

At `k = 10`:

\[
U_{\text{MIDDLE}}=439,498
\]

which is only:

\[
5,802
\]

below HPSS.

At `k = 12`:

\[
U_{\text{MIDDLE}}=458,578
\]

versus:

\[
462,335
\]

for HPSS.

Therefore the research must answer:

> What specifically makes HPSS better than MIDDLE?

This is now one of the most important scientific questions.

If HPSS is significantly more computationally expensive but only marginally improves representation uniqueness over MIDDLE, that trade-off must be quantified.

---

# 48. Recommended Research Metric: Pareto Analysis

Rather than selecting one "winner", evaluate strategies on two axes:

\[
x = \text{hashes/sec}
\]

\[
y = \text{unique representations}
\]

A strategy is attractive if it lies on the Pareto frontier.

A future graph should plot:

```text
unique representation rate
        ^
        |
        |                HPSS
        |          MIDDLE
        |
        |    SUFFIX
        | PREFIX
        +------------------------> throughput
```

The actual positions must be generated from the benchmark data.

This would provide a much stronger engineering argument than a single ranking.

---

# 49. Threats to Validity

## Internal validity

The experiment controls the selected representation supplied to reference hashes, which is strong.

However, timing can be affected by:

- Python interpreter overhead;
- CPU scheduling;
- cache state;
- system load;
- library implementation.

## External validity

One English-word dataset cannot establish general behavior.

## Construct validity

Calling HPSS a "hash function" may be misleading if its primary innovation is actually representation selection plus positional encoding.

The terminology should be carefully defined.

---

# 50. Recommended Terminology

For the paper, consider distinguishing:

### HPSS Selection

The algorithm that selects characters.

### HPSS Representation

The selected character sequence.

### HPSS Positional Encoder

The numerical encoding of that sequence.

### HPSS Hashing Pipeline

The complete:

\[
\text{input}
\rightarrow
\text{selection}
\rightarrow
\text{encoding}
\]

pipeline.

This terminology will make the experimental claims much easier to defend.

---

# 51. Final Assessment

The current `dwyl/english-word` benchmark is significantly more informative than the earlier small-dictionary experiment.

The evidence shows that HPSS has a real and measurable property:

> **It can produce substantially more distinguishable compact representations than simple prefix and suffix selection on a 466,550-entry English-word corpus.**

The strongest results occur around:

```text
k = 8
k = 10
k = 12
```

At `k = 12`, HPSS reaches approximately:

\[
99.10\%
\]

unique representation coverage.

The downstream 64-bit hash comparison also reveals that the dominant collision source in this experiment is the selection stage rather than the final hash stage.

However, the experiment does **not** yet establish HPSS as a superior general-purpose hash function.

The next scientific step should therefore be to test:

1. multiple datasets;
2. random baselines;
3. adversarial inputs;
4. complete `k` curves;
5. hash distribution;
6. avalanche behavior;
7. native-code performance;
8. memory efficiency.

If HPSS continues to show strong representation efficiency across heterogeneous datasets while maintaining acceptable speed and distribution quality, the case for a research publication becomes substantially stronger.

---

# 52. Reproducibility Checklist

Before publication, record:

- [ ] Exact `dwyl/english-word` commit/version
- [ ] SHA-256 of `words.txt`
- [ ] Number of input records
- [ ] Exact HPSS source code
- [ ] Exact benchmark source code
- [ ] Python version
- [ ] CPU model
- [ ] Operating system
- [ ] Reference-library versions
- [ ] Compiler versions if native implementations are added
- [ ] Random seeds
- [ ] Number of timing repetitions
- [ ] Raw CSV results
- [ ] Scripts used to generate every figure
- [ ] Scripts used to generate every table

---

# 53. Conclusion

The `dwyl/english-word` experiment provides strong preliminary evidence that HPSS is more than an arbitrary character-selection heuristic.

On a 466,550-entry real-world English-word corpus, HPSS:

- substantially outperforms PREFIX and SUFFIX in unique representation count for moderate and large `k`;
- reaches **392,351 unique representations at `k=8`**;
- reaches **445,300 unique representations at `k=10`**;
- reaches **462,335 unique representations at `k=12`**;
- reduces the representation collision-entry rate to **0.9034% at `k=12`**;
- produces only **9,714 collision pairs at `k=12`**;
- introduces no additional observed collisions in the tested downstream 64-bit hash functions;
- but is slower than MurmurHash3 and xxHash64 in the supplied Python implementation.

The most scientifically responsible interpretation is therefore:

\[
\boxed{
\text{HPSS shows promising compact-representation behavior,
not yet proven superiority as a universal hash function.}
}
\]

The next stage should focus on establishing whether this behavior is a genuine general property of the HPSS algorithm or primarily an advantage on English lexical structure.

If the same trend survives heterogeneous and adversarial datasets, the research claim becomes considerably stronger.

---

## Appendix A — Raw Benchmark Configuration

```python
DICTIONARY = "dictionaries/words.txt"

K_VALUES = [2, 4, 6, 8, 10, 12]

REPETITIONS = 5
```

The benchmark lowercases input keys and encodes selected representations using UTF-8 before passing them to the reference byte-oriented hash functions.

---

## Appendix B — Collision Formula Reference

For input count:

\[
N
\]

and unique values:

\[
U
\]

collision entries:

\[
C_E=N-U
\]

collision-entry rate:

\[
R_E=\frac{N-U}{N}
\]

For frequency groups `f_i`:

\[
C_P
=
\sum_i
\frac{f_i(f_i-1)}{2}
\]

Maximum collision group:

\[
C_{\max}=\max_i f_i
\]

---

## Appendix C — Key Result Table

| k | Strategy | Unique | Collision entries | Rate | Pairs | Max group |
|---:|---|---:|---:|---:|---:|---:|
| 2 | PREFIX | 828 | 465,722 | 99.8225% | 1,165,447,482 | 20,575 |
| 2 | SUFFIX | 817 | 465,733 | 99.8249% | 2,425,732,073 | 35,646 |
| 2 | HPSS | 837 | 465,713 | 99.8206% | 617,795,432 | 9,310 |
| 2 | MIDDLE | 898 | 465,652 | 99.8075% | 555,617,187 | 9,040 |
| 4 | PREFIX | 38,694 | 427,856 | 91.7064% | 50,042,271 | 4,055 |
| 4 | SUFFIX | 38,412 | 428,138 | 91.7668% | 202,969,576 | 10,165 |
| 4 | HPSS | 46,895 | 419,655 | 89.9486% | 49,837,286 | 5,118 |
| 4 | MIDDLE | 64,759 | 401,791 | 86.1196% | 9,394,049 | 535 |
| 6 | PREFIX | 184,988 | 281,562 | 60.3498% | 4,935,894 | 1,027 |
| 6 | SUFFIX | 189,260 | 277,290 | 59.4341% | 18,244,102 | 2,694 |
| 6 | HPSS | 250,828 | 215,722 | 46.2377% | 3,999,078 | 592 |
| 6 | MIDDLE | 279,479 | 187,071 | 40.0967% | 759,469 | 152 |
| 8 | PREFIX | 325,545 | 141,005 | 30.2229% | 546,516 | 139 |
| 8 | SUFFIX | 333,801 | 132,749 | 28.4533% | 2,527,296 | 952 |
| 8 | HPSS | 392,351 | 74,199 | 15.9038% | 498,441 | 355 |
| 8 | MIDDLE | 389,992 | 76,558 | 16.4094% | 167,865 | 54 |
| 10 | PREFIX | 407,315 | 59,235 | 12.6964% | 133,334 | 31 |
| 10 | SUFFIX | 413,765 | 52,785 | 11.3139% | 251,730 | 199 |
| 10 | HPSS | 445,300 | 21,250 | 4.5547% | 76,200 | 147 |
| 10 | MIDDLE | 439,498 | 27,052 | 5.7983% | 43,317 | 27 |
| 12 | PREFIX | 445,322 | 21,228 | 4.5500% | 37,659 | 28 |
| 12 | SUFFIX | 449,753 | 16,797 | 3.6003% | 43,366 | 111 |
| 12 | HPSS | 462,335 | 4,215 | 0.9034% | 9,714 | 63 |
| 12 | MIDDLE | 458,578 | 7,972 | 1.7087% | 10,406 | 12 |

---

## Appendix D — Interpretation in One Sentence

**The current evidence supports HPSS as a promising compact, structure-aware representation strategy whose strongest demonstrated advantage is information preservation during character selection, rather than raw hash-function speed or proven universal collision resistance.**
