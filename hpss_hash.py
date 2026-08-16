"""HPSS: Hybrid Prefix-Suffix Selection hashing.

The research implementation separates two operations:

1. selection: retain k characters from the input key;
2. encoding: map the selected representation to an integer.

The default positional encoder is injective over finite Unicode strings
when represented as an arbitrary-precision Python integer. It is therefore
not a fixed-width 64-bit hash function.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

UNICODE_BASE = 0x110000
MASK64 = (1 << 64) - 1


class UnsupportedCharacterError(ValueError):
    """Raised when a closed alphabet cannot encode a character."""


def make_digit_table(alphabet: str) -> dict[str, int]:
    if len(set(alphabet)) != len(alphabet):
        raise ValueError("alphabet contains duplicate characters")
    if not alphabet:
        raise ValueError("alphabet must not be empty")
    return {ch: i + 1 for i, ch in enumerate(alphabet)}


def hpss_positional_hash(text: str, alphabet: str | None = None, *, on_unknown: str = "raise") -> int:
    """Encode a string with positive positional digits."""
    if on_unknown not in {"raise", "skip"}:
        raise ValueError("on_unknown must be 'raise' or 'skip'")
    if alphabet is None:
        h = 0
        for ch in text:
            h = h * UNICODE_BASE + ord(ch) + 1
        return h
    digits = make_digit_table(alphabet)
    base = len(alphabet)
    h = 0
    for ch in text:
        digit = digits.get(ch)
        if digit is None:
            if on_unknown == "skip":
                continue
            raise UnsupportedCharacterError(f"character {ch!r} is not in the configured alphabet")
        h = h * base + digit
    return h


@dataclass(frozen=True)
class CompiledEncoder:
    """Reusable positional encoder."""
    alphabet: str | None = None
    on_unknown: str = "raise"

    def __post_init__(self) -> None:
        if self.on_unknown not in {"raise", "skip"}:
            raise ValueError("on_unknown must be 'raise' or 'skip'")
        if self.alphabet is None:
            object.__setattr__(self, "_digits", None)
            object.__setattr__(self, "_base", UNICODE_BASE)
        else:
            object.__setattr__(self, "_digits", make_digit_table(self.alphabet))
            object.__setattr__(self, "_base", len(self.alphabet))

    def __call__(self, text: str) -> int:
        if self.alphabet is None:
            h = 0
            for ch in text:
                h = h * self._base + ord(ch) + 1
            return h
        h = 0
        for ch in text:
            digit = self._digits.get(ch)
            if digit is None:
                if self.on_unknown == "skip":
                    continue
                raise UnsupportedCharacterError(f"character {ch!r} is not in the configured alphabet")
            h = h * self._base + digit
        return h


# ----------------------------------------------------------------------
# Selection strategies
# ----------------------------------------------------------------------

def select_prefix(word: str, k: int) -> str:
    if k < 0:
        raise ValueError("k must be non-negative")
    return word[:k]


def select_suffix(word: str, k: int) -> str:
    if k < 0:
        raise ValueError("k must be non-negative")
    return word[-k:] if len(word) > k else word


def select_hpss(word: str, k: int) -> str:
    """Select k characters from both ends.

    Even k: k/2 from the front and k/2 from the back.
    Odd k: floor(k/2) from the front and ceil(k/2) from the back.

    Thus k=5 means 2 characters from the front and 3 from the back.
    """
    if k < 0:
        raise ValueError("k must be non-negative")
    if len(word) <= k:
        return word
    if k == 0:
        return ""
    front = k // 2
    back = k - front
    return word[:front] + word[-back:]


def select_middle(word: str, k: int) -> str:
    if k < 0:
        raise ValueError("k must be non-negative")
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


# ----------------------------------------------------------------------
# Reference hash functions
# ----------------------------------------------------------------------

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
        raise RuntimeError("mmh3 is not installed; install the benchmark dependencies") from exc
    value, _ = mmh3.hash64(data, seed=0, signed=False)
    return value


def hash_xxhash64(data: bytes) -> int:
    try:
        import xxhash
    except ImportError as exc:
        raise RuntimeError("xxhash is not installed; install the benchmark dependencies") from exc
    return xxhash.xxh64(data).intdigest()


REFERENCE_HASHES: dict[str, Callable[[bytes], int]] = {
    "FNV1A64": hash_fnv1a64,
    "MURMUR3_64": hash_murmur3_64,
    "XXHASH64": hash_xxhash64,
}


@dataclass(frozen=True)
class HPSSHasher:
    """Complete HPSS pipeline: normalize, select, then encode."""
    k: int = 8
    strategy: str = "HPSS"
    alphabet: str | None = None

    def __post_init__(self) -> None:
        if self.k < 0:
            raise ValueError("k must be non-negative")
        if self.strategy not in SELECTION_STRATEGIES:
            raise ValueError(f"unknown strategy: {self.strategy}")

    def __call__(self, word: str) -> int:
        representation = SELECTION_STRATEGIES[self.strategy](word.lower(), self.k)
        return hpss_positional_hash(representation, self.alphabet)

    def table_index(self, word: str, table_size: int) -> int:
        if table_size <= 0:
            raise ValueError("table_size must be positive")
        return self(word) % table_size


if __name__ == "__main__":
    examples = ["abcde", "abcdef", "don't", "test-case", "hello_world", "中"]
    hasher = HPSSHasher(k=5)
    print("HPSS smoke test")
    print("k=5 => floor(k/2)=2 front + ceil(k/2)=3 back")
    for word in examples:
        print(f"{word!r} -> {select_hpss(word, 5)!r} -> {hasher(word)}")
