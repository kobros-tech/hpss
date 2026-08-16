"""
======================================================================
HPSS — Hybrid Prefix-Suffix Selection hashing
======================================================================

This module is the CLEANED-UP, FINAL version of the research carried
out across stage3 -> stage5 of the original experiment log (see
RESEARCH_LOG.md). It fixes every bug that was found along the way and
keeps only the parts of the idea that actually held up under testing.

--------------------------------------------------------------------
THE IDEA
--------------------------------------------------------------------
Hashing a whole word costs O(len(word)). Most of the discriminating
information in an English word is concentrated near the start and
end of the word (prefixes and suffixes carry most of the entropy;
English words share a LOT of middle substrings — "-tion", "-ing",
"-ology", etc). So instead of hashing every character, HPSS *selects*
a small, fixed-size subset of characters (by default: first k/2 +
last k/2), and only hashes that subset.

This trades a small amount of accuracy (more "representation
collisions" because two words can share the same first/last
characters) for a large amount of speed (fewer characters to touch
per word), which matters for very large dictionaries or streaming
input.

--------------------------------------------------------------------
BUGS FOUND AND FIXED DURING THE RESEARCH
--------------------------------------------------------------------

BUG 1 — a=0 encoding (stage3 / stage4, fixed in stage4b)
    The first positional encoder mapped 'a' -> 0. Under a plain
    base-26 Horner scheme (h = h*26 + value), a leading 'a' (value 0)
    contributes NOTHING to the hash. That means:

        hash("b")  == hash("ab") == hash("aab") == ...

    FIX: shift the alphabet so 'a' -> 1, 'b' -> 2, ..., 'z' -> 26.
    This turns the encoder into a *bijective base-26 numeral system*
    (the same scheme spreadsheets use for column names: A, B, ...,
    Z, AA, AB, ...). Bijective base-k numerations are a well known,
    provably injective mapping from arbitrary-length digit strings
    to the natural numbers (Smullyan 1961; Böhm 1964) — i.e. for a
    fixed, closed alphabet, NO two different strings can ever produce
    the same integer, regardless of length.

BUG 2 — out-of-alphabet characters (found while cleaning up this
    project; NOT caught in the original stage3-5 experiments)
    The bijective-base-26 injectivity guarantee only holds if every
    character actually maps to a digit in [1, 26]. The CS50 "large"
    dictionary was assumed to be pure a-z, but it is not:

        >>> "'" in open("dictionaries/large").read()
        True

    8,611 of 143,091 entries (~6%) contain an apostrophe
    ("don't", "abbott's", "y'all", ...). The old encoder computed
    ord("'") - ord("a") + 1 = -57, a NEGATIVE "digit". A negative
    digit breaks the bijective-numeral guarantee (it reintroduces the
    "carry" ambiguity the a=1 fix was designed to remove), and it
    produced 50 genuine hash collisions between different
    representations that should *not* have collided
    (e.g. "conseous" from both "consanguineous" and "consentaneous"
    under HPSS k=8 — see RESEARCH_LOG.md for the full derivation).

    FIX (this file): the alphabet is explicit and closed
    (ALPHABET below). Any character outside of it is treated through
    a documented, deterministic fallback instead of silently going
    negative. Default alphabet is a-z plus apostrophe (27 symbols),
    which is exactly what CS50's "large" dictionary needs. Swap in
    a different ALPHABET for other corpora.

--------------------------------------------------------------------
WHAT THIS MODULE IS -- AND ISN'T
--------------------------------------------------------------------
- It IS a fast, exact, order-preserving encoder for short character
  selections drawn from a small closed alphabet. Two different
  selections never collide (see test_no_collisions.py).
- It is NOT a fixed-width hash. Output grows with the number of
  selected characters (though for realistic k this stays well inside
  64 bits — see RESEARCH_LOG.md for the numeric bound). Reduce with
  `% table_size` (ideally a prime table size) before using as a
  hash-table index, same as any other hash.
- It is NOT a cryptographic hash and NOT a general drop-in replacement
  for FNV-1a / MurmurHash3 / xxHash on arbitrary binary data. It is a
  purpose-built encoder for a small, known alphabet (English words,
  identifiers, etc).
- Its real, measured advantage is TOUCHING FEWER BYTES PER KEY, not
  better statistical mixing. See RESULTS.md: at equal k, established
  hash functions applied to the *same* HPSS-selected characters
  produce equal-or-slightly-better collision rates than the pure
  positional encoder, because the positional encoder is a *direct
  numeral encoding*, not a mixing function. Its virtue is that it is
  injective for a closed alphabet and can be computed with fewer
  operations per character than FNV/Murmur/xxHash's finalization
  steps -- not that it beats them at randomness.
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from typing import Callable, Sequence

# ======================================================================
# ALPHABET
# ======================================================================
# Closed, ordered alphabet. Position in this string IS the digit value
# minus 1 (so the first symbol maps to digit 1, per bijective base-k).
# Default covers CS50's "large" dictionary: lowercase letters + the
# apostrophe used in contractions/possessives ("don't", "cook's").
# For a pure a-z corpus, use ALPHABET_PLAIN instead.

ALPHABET_PLAIN = string.ascii_lowercase                 # 26 symbols
ALPHABET_CS50 = string.ascii_lowercase + "'"             # 27 symbols

DEFAULT_ALPHABET = ALPHABET_CS50


class UnsupportedCharacterError(ValueError):
    """Raised when a character outside the configured alphabet is hashed."""


def make_digit_table(alphabet: str) -> dict[str, int]:
    """digit(char) in [1, len(alphabet)] -- bijective base-len(alphabet)."""
    return {ch: i + 1 for i, ch in enumerate(alphabet)}


# ======================================================================
# CORE HPSS POSITIONAL ENCODER  (bug-fixed, closed-alphabet version)
# ======================================================================

def hpss_positional_hash(
    text: str,
    alphabet: str = DEFAULT_ALPHABET,
    *,
    on_unknown: str = "raise",
) -> int:
    """
    Bijective base-N positional encoding of `text`.

        h = 0
        for ch in text:
            h = h * N + digit(ch)          # digit in [1, N]

    Provably collision-free for any two different strings drawn from
    `alphabet` (any length, any content) -- see module docstring.

    on_unknown:
        "raise"  -- raise UnsupportedCharacterError (default, safest)
        "skip"   -- silently drop characters outside the alphabet
                    (this is what the ORIGINAL buggy code effectively
                    did via str.encode("ascii", errors="ignore") plus
                    an unchecked digit formula -- kept here only for
                    backward comparison, not recommended)

    NOTE ON PERFORMANCE: this convenience function rebuilds the digit
    lookup table on every call, which is fine for one-off use but
    unfair in a tight hashing loop. For benchmarking or hashing many
    words, build a `CompiledEncoder` once and reuse it (see below) --
    the original stage3-5 scripts made exactly this mistake, which
    understated the encoder's real speed.
    """
    digits = make_digit_table(alphabet)
    n = len(alphabet)
    h = 0
    for ch in text:
        d = digits.get(ch)
        if d is None:
            if on_unknown == "skip":
                continue
            raise UnsupportedCharacterError(
                f"character {ch!r} is not in the configured alphabet "
                f"({alphabet!r}); pass a wider `alphabet=` or "
                f"on_unknown='skip'"
            )
        h = h * n + d
    return h


@dataclass(frozen=True)
class CompiledEncoder:
    """Same encoding as `hpss_positional_hash`, with the digit table
    built exactly once. Use this in any performance-sensitive loop.
    """

    alphabet: str = DEFAULT_ALPHABET
    on_unknown: str = "raise"

    def __post_init__(self):
        object.__setattr__(self, "_digits", make_digit_table(self.alphabet))
        object.__setattr__(self, "_n", len(self.alphabet))

    def __call__(self, text: str) -> int:
        digits = self._digits
        n = self._n
        h = 0
        for ch in text:
            d = digits.get(ch)
            if d is None:
                if self.on_unknown == "skip":
                    continue
                raise UnsupportedCharacterError(
                    f"character {ch!r} is not in the configured alphabet "
                    f"({self.alphabet!r})"
                )
            h = h * n + d
        return h


# ======================================================================
# SELECTION STRATEGIES
# ======================================================================
# A selection strategy reduces a word to <= k characters *before*
# hashing. This is the actual novel/tunable part of the design; the
# encoder above is deliberately dumb and exact.

def select_prefix(word: str, k: int) -> str:
    return word[:k]


def select_suffix(word: str, k: int) -> str:
    return word if len(word) <= k else word[-k:]


def select_hpss(word: str, k: int) -> str:
    """Hybrid Prefix-Suffix Selection: first k/2 chars + last k/2 chars.

    Falls back to a plain prefix for odd k (can't split evenly) and
    for words no longer than k (nothing to save).
    """
    if len(word) <= k:
        return word
    if k % 2 == 1:
        return word[:k]
    half = k // 2
    return word[:half] + word[-half:]


def select_middle(word: str, k: int) -> str:
    if len(word) <= k:
        return word
    start = (len(word) - k) // 2
    return word[start:start + k]


SELECTION_STRATEGIES: dict[str, Callable[[str, int], str]] = {
    "PREFIX": select_prefix,
    "SUFFIX": select_suffix,
    "HPSS": select_hpss,
    "MIDDLE": select_middle,
}


# ======================================================================
# REFERENCE / COMPARISON HASH FUNCTIONS
# ======================================================================
# These are the established, well-studied hash functions HPSS is
# benchmarked against. All three take `bytes` and return a 64-bit
# unsigned integer.

MASK64 = (1 << 64) - 1


def hash_fnv1a64(data: bytes) -> int:
    h = 14695981039346656037
    prime = 1099511628211
    for byte in data:
        h ^= byte
        h = (h * prime) & MASK64
    return h


def hash_murmur3_64(data: bytes) -> int:
    try:
        import mmh3
    except ImportError as exc:
        raise RuntimeError(
            "mmh3 is not installed. Install with:\n"
            "    python3 -m pip install mmh3"
        ) from exc
    value, _ = mmh3.hash64(data, seed=0, signed=False)
    return value


def hash_xxhash64(data: bytes) -> int:
    try:
        import xxhash
    except ImportError as exc:
        raise RuntimeError(
            "xxhash is not installed. Install with:\n"
            "    python3 -m pip install xxhash"
        ) from exc
    return xxhash.xxh64(data).intdigest()


REFERENCE_HASHES: dict[str, Callable[[bytes], int]] = {
    "FNV1A64": hash_fnv1a64,
    "MURMUR3_64": hash_murmur3_64,
    "XXHASH64": hash_xxhash64,
}


# ======================================================================
# CONVENIENCE: full pipeline
# ======================================================================

@dataclass(frozen=True)
class HPSSHasher:
    """Bundles a selection strategy + the corrected positional encoder."""

    k: int = 8
    strategy: str = "HPSS"
    alphabet: str = DEFAULT_ALPHABET

    def __call__(self, word: str) -> int:
        selector = SELECTION_STRATEGIES[self.strategy]
        rep = selector(word.lower(), self.k)
        return hpss_positional_hash(rep, self.alphabet)

    def table_index(self, word: str, table_size: int) -> int:
        """Reduce the (unbounded) HPSS value to a table slot.

        Use a prime `table_size` to avoid the usual modulo-power-of-two
        pitfalls of positional/polynomial hashes.
        """
        return self(word) % table_size


if __name__ == "__main__":
    # Tiny smoke test / demo.
    h = HPSSHasher(k=8, strategy="HPSS")
    for w in ["hash", "table", "algorithm", "don't", "abbott's"]:
        print(f"{w!r:>12} -> {h(w)}")

    # Characters outside the configured alphabet are rejected loudly
    # instead of silently corrupting the encoding (this is BUG 2 from
    # the module docstring, fixed):
    try:
        h("cs50")
    except UnsupportedCharacterError as exc:
        print(f"\n(expected) rejected 'cs50': {exc}")
