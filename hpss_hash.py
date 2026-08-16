"""
======================================================================
HPSS — Hybrid Prefix-Suffix Selection hashing
======================================================================

HPSS selects a small number of characters from a key before encoding.

The default selection strategy is:

    first k/2 characters + last k/2 characters

The positional encoder is collision-free for distinct character
sequences because every Unicode code point is mapped to a positive
digit:

    digit(c) = ord(c) + 1

and the encoding uses base:

    UNICODE_BASE = 0x110000 = 1,114,112

Thus:

    1 <= digit(c) <= UNICODE_BASE

This avoids the historical a=0 and negative-digit bugs while allowing
letters, numbers, punctuation, symbols, and Unicode characters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


# ======================================================================
# UNICODE CHARACTER ENCODING
# ======================================================================

# Unicode code points are in the range:
#
#     0 .. 0x10FFFF
#
# Therefore there are exactly:
#
#     0x110000 = 1,114,112
#
# possible code points.

UNICODE_BASE = 0x110000


class UnsupportedCharacterError(ValueError):
    """Kept for API compatibility.

    The default Unicode encoder accepts every valid Python Unicode
    character, so this exception normally isn't raised.
    """
    pass


def make_digit_table(alphabet: str) -> dict[str, int]:
    """
    Build a positive digit mapping for an explicit alphabet.

    This function is retained for compatibility with the earlier
    closed-alphabet implementation.

    Characters receive digits:

        first character  -> 1
        second character -> 2
        ...

    The alphabet must not contain duplicate characters.
    """

    if len(set(alphabet)) != len(alphabet):
        raise ValueError("alphabet contains duplicate characters")

    return {ch: i + 1 for i, ch in enumerate(alphabet)}


def hpss_positional_hash(
    text: str,
    alphabet: str | None = None,
    *,
    on_unknown: str = "raise",
) -> int:
    """
    Collision-free positional encoding of a Unicode string.

    DEFAULT MODE
    ------------

    If alphabet=None, every Unicode character is encoded directly:

        digit(c) = ord(c) + 1

    and:

        base = 1,114,112

    Encoding:

        h = 0
        for ch in text:
            h = h * UNICODE_BASE + (ord(ch) + 1)

    Since every digit is in:

        [1, UNICODE_BASE]

    distinct strings have distinct encodings.

    This supports:

        letters
        digits
        punctuation
        symbols
        Unicode characters

    Examples:

        'a'
        '2'
        "'"
        '-'
        '_'
        '@'
        '#'
        'é'
        '中'

    all work without requiring an alphabet update.

    ------------------------------------------------------------------
    OPTIONAL CLOSED ALPHABET MODE
    ------------------------------------------------------------------

    If alphabet is supplied, the historical explicit-alphabet mode
    remains available.

    Example:

        hpss_positional_hash("hello", "abcdefghijklmnopqrstuvwxyz")

    In this mode every character must occur in the supplied alphabet.

    `on_unknown`:

        "raise" -> raise UnsupportedCharacterError
        "skip"  -> ignore characters outside the alphabet

    The default "raise" behavior is recommended.
    """

    # --------------------------------------------------------------
    # GENERAL UNICODE MODE
    # --------------------------------------------------------------

    if alphabet is None:
        h = 0

        for ch in text:
            digit = ord(ch) + 1
            h = h * UNICODE_BASE + digit

        return h

    # --------------------------------------------------------------
    # EXPLICIT CLOSED-ALPHABET MODE
    # --------------------------------------------------------------

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
                f"use the default Unicode mode"
            )

        h = h * n + d

    return h


# ======================================================================
# COMPILED ENCODER
# ======================================================================

@dataclass(frozen=True)
class CompiledEncoder:
    """
    High-performance reusable positional encoder.

    With alphabet=None, uses the Unicode code-point encoder directly.
    This is the recommended mode for the research benchmark because
    it supports arbitrary letters, numbers, punctuation and symbols
    without rebuilding a lookup table.
    """

    alphabet: str | None = None
    on_unknown: str = "raise"

    def __post_init__(self):

        if self.alphabet is not None:
            object.__setattr__(
                self,
                "_digits",
                make_digit_table(self.alphabet),
            )

            object.__setattr__(
                self,
                "_base",
                len(self.alphabet),
            )

        else:
            object.__setattr__(
                self,
                "_digits",
                None,
            )

            object.__setattr__(
                self,
                "_base",
                UNICODE_BASE,
            )

    def __call__(self, text: str) -> int:

        # ----------------------------------------------------------
        # GENERAL UNICODE MODE
        # ----------------------------------------------------------

        if self.alphabet is None:

            base = UNICODE_BASE
            h = 0

            for ch in text:
                h = h * base + ord(ch) + 1

            return h

        # ----------------------------------------------------------
        # CLOSED ALPHABET MODE
        # ----------------------------------------------------------

        digits = self._digits
        base = self._base

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

            h = h * base + d

        return h


# ======================================================================
# SELECTION STRATEGIES
# ======================================================================

def select_prefix(word: str, k: int) -> str:
    return word[:k]


def select_suffix(word: str, k: int) -> str:
    return word if len(word) <= k else word[-k:]


def select_hpss(word: str, k: int) -> str:
    """
    Hybrid Prefix-Suffix Selection.

    For even k:

        first k/2 + last k/2

    For odd k, falls back to the prefix.

    Words shorter than or equal to k are returned unchanged.
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
# REFERENCE HASH FUNCTIONS
# ======================================================================

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
            "    python3.11 -m pip install mmh3"
        ) from exc

    value, _ = mmh3.hash64(
        data,
        seed=0,
        signed=False,
    )

    return value


def hash_xxhash64(data: bytes) -> int:

    try:
        import xxhash

    except ImportError as exc:

        raise RuntimeError(
            "xxhash is not installed. Install with:\n"
            "    python3.11 -m pip install xxhash"
        ) from exc

    return xxhash.xxh64(data).intdigest()


REFERENCE_HASHES: dict[str, Callable[[bytes], int]] = {
    "FNV1A64": hash_fnv1a64,
    "MURMUR3_64": hash_murmur3_64,
    "XXHASH64": hash_xxhash64,
}


# ======================================================================
# FULL HPSS PIPELINE
# ======================================================================

@dataclass(frozen=True)
class HPSSHasher:

    k: int = 8
    strategy: str = "HPSS"
    alphabet: str | None = None

    def __call__(self, word: str) -> int:

        selector = SELECTION_STRATEGIES[self.strategy]

        rep = selector(
            word.lower(),
            self.k,
        )

        return hpss_positional_hash(
            rep,
            self.alphabet,
        )

    def table_index(
        self,
        word: str,
        table_size: int,
    ) -> int:

        return self(word) % table_size


# ======================================================================
# SMOKE TEST
# ======================================================================

if __name__ == "__main__":

    h = HPSSHasher(
        k=8,
        strategy="HPSS",
    )

    test_words = [
        "hash",
        "table",
        "algorithm",
        "don't",
        "abbott's",
        "abc123",
        "test-case",
        "hello_world",
        "foo@bar",
        "C++",
        "version2.0",
        "100%",
    ]

    print("=" * 70)
    print("HPSS UNICODE ENCODER TEST")
    print("=" * 70)

    for word in test_words:

        value = h(word)

        print(
            f"{word!r:>20} -> {value}"
        )

    print("\nAll test characters accepted.")