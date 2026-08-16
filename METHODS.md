# Experimental Methodology

## 1. Research question

The experiment asks whether Hybrid Prefix-Suffix Selection (HPSS) retains more
information in a compact textual representation than simple positional
selectors, and whether the proposed positional encoder introduces additional
collisions among the representations produced by those selectors.

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

## 5. Encoders

The proposed positional encoder maps each Unicode code point `c` to
`ord(c)+1` and uses base `0x110000`. It is implemented with Python arbitrary-
precision integers.

Reference encoders are FNV-1a 64-bit, MurmurHash3 64-bit, and xxHash64.
Reference encoders receive the selected representation encoded as UTF-8.

## 6. Collision metrics

For `n` input entries and `U` distinct values:

```text
collision_entries = n - U
collision_entry_rate = (n - U) / n
```

For a frequency group of size `f`, the number of colliding pairs is:

```text
f(f-1)/2
```

and total collision pairs are the sum across all groups. The largest group is
also reported.

## 7. Timing

Each encoder is applied to the complete representation list five times. The
median elapsed time is reported together with entries per second. Timings are
hardware-, Python-version-, and system-load-dependent and must not be treated
as universal performance rankings.

## 8. Data handling

The included dictionary is read as UTF-8. Empty lines are discarded and each
remaining line is stripped and lowercased. Reference hashes use UTF-8 bytes;
no ASCII `errors="ignore"` conversion is used.

## 9. Interpretation rule

A collision already present in `R(w,k)` is a representation collision. It is
not evidence of a collision weakness in the downstream encoder. A downstream
hash collision is only counted when two distinct representations map to the
same encoded/hash value.

## 10. Scope and limitations

The experiment is empirical. Zero observed collisions in a finite benchmark
are not a proof of universal collision resistance for fixed-width hashes.
The positional encoder is mathematically injective over finite strings in its
arbitrary-precision representation, but its integer size grows with the
representation length and therefore it is not directly equivalent to a
fixed-width 64-bit hash.

Results from one dictionary cannot establish performance or collision
behavior for all languages, workloads, key distributions, or adversarial
inputs.
