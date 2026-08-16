# Experimental Methodology

## 1. Research question

The experiment asks whether Hybrid Prefix-Suffix Selection (HPSS) retains more
information in a compact textual representation than simple positional
selectors, and under which key distributions boundary selection is useful.
The study also tests whether the proposed positional encoder introduces any
additional collisions after selection.

## 2. Pipeline

For each normalized input word `w`:

```text
w -> selection R(w,k) -> representation collision analysis -> encoder -> hash collision analysis
```

The two collision stages are intentionally reported separately.

## 3. HPSS definition

For `len(w) <= k`, HPSS returns `w` unchanged.

For `len(w) > k`, define:

```text
front = floor(k / 2)
back  = k - front = ceil(k / 2)
```

and

```text
HPSS(w,k) = w[:front] + w[-back:]
```

Therefore:

- `k=2` -> 1 front + 1 back
- `k=4` -> 2 front + 2 back
- `k=5` -> 2 front + 3 back
- `k=7` -> 3 front + 4 back

The odd-k rule is part of the algorithm definition, not a benchmark-only
convention.

## 4. Baselines

The benchmark includes `PREFIX`, `SUFFIX`, and `MIDDLE` selectors. The same
selected representation is then supplied to each downstream encoder.

## 5. Allocation ablation

The balanced HPSS rule is only one member of a larger family:

```text
R(k,p) = prefix(p) + suffix(k-p),  0 <= p <= k
```

For each tested `k`, the research benchmark evaluates every allocation from
`0+(k)` through `k+0`. This directly tests whether the balanced split is
actually optimal rather than assuming that it is.

## 6. Encoders

The proposed positional encoder maps each Unicode code point `c` to
`ord(c)+1` and uses base `0x110000`. It is implemented with Python arbitrary-
precision integers.

Reference encoders are FNV-1a 64-bit, MurmurHash3 64-bit, and xxHash64.
Reference encoders receive the selected representation encoded as UTF-8.

The positional encoder is treated as an **encoding control**, not as evidence
that HPSS is a universally superior fixed-width hash function.

## 7. Collision metrics

For `n` input entries and `U` distinct values:

```text
collision_entries = n - U
collision_entry_rate = (n - U) / n
```

For a frequency group of size `f`, the number of colliding pairs is:

```text
f(f-1)/2
```

and total collision pairs are the sum across all groups. The largest group and
collision-group-size distribution are also reported.

## 8. Datasets and controls

The repository dictionary is the primary real-world lexical dataset. The
research benchmark additionally generates deterministic controls for:

- random lowercase-alphanumeric strings;
- structured identifiers containing repeated prefix, region, and numeric
  fields.

The synthetic controls use a fixed seed so their results are reproducible.
The benchmark architecture also accepts additional datasets by adapting the
same `list[str]` interface, allowing independent-language dictionaries and
application-specific key corpora to be added without changing the metrics.

These controls are important because an improvement on English words alone
could reflect English morphology rather than a general property of boundary
selection.

## 9. Input-length analysis

The research benchmark stratifies the lexical dataset by input length and
compares selector behavior at representative `k` values. This separates the
fixed representation budget from the length distribution of the source data.

## 10. Statistical stability

For paired comparisons, the research utilities provide a deterministic
bootstrap procedure for the mean within-item difference and a percentile 95%
confidence interval. Confidence intervals should be reported when a paper
compares sampled subsets or repeated datasets; they should not be used to
pretend that the full deterministic dictionary is a random sample of all
possible words.

## 11. Timing

Each encoder is applied to the complete representation list five times. The
median elapsed time is reported together with entries per second. Timings are
hardware-, Python-version-, and system-load-dependent and must not be treated
as universal performance rankings.

## 12. Data handling

The included dictionary is read as UTF-8. Empty lines are discarded and each
remaining line is stripped and lowercased. Reference hashes use UTF-8 bytes;
no ASCII `errors="ignore"` conversion is used.

## 13. Interpretation rule

A collision already present in `R(w,k)` is a representation collision. It is
not evidence of a collision weakness in the downstream encoder. A downstream
hash collision is only counted when two distinct representations map to the
same encoded/hash value.

## 14. Scope and limitations

The experiment is empirical. Zero observed collisions in a finite benchmark
are not a proof of universal collision resistance for fixed-width hashes.
The positional encoder is mathematically injective over finite strings in its
arbitrary-precision representation, but its integer size grows with the
representation length and therefore it is not directly equivalent to a
fixed-width 64-bit hash.

Results from one dictionary cannot establish performance or collision
behavior for all languages, workloads, key distributions, or adversarial
inputs. In particular, the current synthetic controls are deliberately
simple and should be supplemented by independently sourced non-English and
application-specific datasets before making broad generalization claims.
