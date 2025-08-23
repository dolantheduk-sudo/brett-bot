# utils/rng.py
from __future__ import annotations

import os
import random
from typing import Sequence, TypeVar

T = TypeVar("T")

__all__ = [
    "set_seed",
    "roll",
    "roll_between",
    "adv",
    "dis",
    "percent",
    "wchoice",
    "gauss_bounded",
    "dice",
    "nudge",
    "chance_from_stat",
]

# Single RNG instance so outcomes are consistent across imports
_RNG = random.Random()

# Optional deterministic seeding via env (nice for tests or dev)
_env_seed = os.getenv("RNG_SEED")
if _env_seed is not None:
    try:
        _RNG.seed(int(_env_seed))
    except Exception:
        _RNG.seed(_env_seed)


def set_seed(seed: int | str) -> None:
    """Deterministically seed the RNG (primarily for tests)."""
    _RNG.seed(seed)


def roll(n: int = 100) -> int:
    """Return an integer in [1, n]."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return _RNG.randint(1, n)


def roll_between(lo: int, hi: int) -> int:
    """Return an integer in [lo, hi] (inclusive)."""
    if lo > hi:
        lo, hi = hi, lo
    return _RNG.randint(lo, hi)


def adv(n: int = 100) -> int:
    """Roll with advantage: max(roll(n), roll(n))."""
    a = roll(n)
    b = roll(n)
    return a if a >= b else b


def dis(n: int = 100) -> int:
    """Roll with disadvantage: min(roll(n), roll(n))."""
    a = roll(n)
    b = roll(n)
    return a if a <= b else b


def percent(p: float) -> bool:
    """Return True with probability p (0..1)."""
    if p <= 0:
        return False
    if p >= 1:
        return True
    return _RNG.random() < p


def wchoice(items: Sequence[T], weights: Sequence[float]) -> T:
    """
    Weighted choice over items using the given weights.
    Lengths must match and all weights non-negative.
    """
    if len(items) != len(weights) or not items:
        raise ValueError("items and weights must be same length and non-empty")
    if any(w < 0 for w in weights):
        raise ValueError("weights must be non-negative")

    total = float(sum(weights))
    if total <= 0:
        # fall back to uniform if weights all zero
        return _RNG.choice(list(items))

    r = _RNG.random() * total
    c = 0.0
    for item, w in zip(items, weights):
        c += w
        if r <= c:
            return item
    # floating-point safety net
    return items[-1]


def gauss_bounded(mean: float, sd: float, lo: float, hi: float) -> float:
    """Gaussian sample clamped into [lo, hi]."""
    if lo > hi:
        lo, hi = hi, lo
    if sd <= 0:
        # degenerate: return clamped mean
        return max(lo, min(hi, mean))
    x = _RNG.gauss(mean, sd)
    return min(hi, max(lo, x))


def dice(expr: str) -> int:
    """
    Parse and roll simple dice expressions like:
      "d20", "2d6", "3d6+2", "4d8-1"
    Returns the total integer result.

    Grammar (simple):
      <count>d<sides> [ +|- <modifier> ]
    """
    s = expr.strip().lower().replace(" ", "")
    if "d" not in s:
        # treat as a flat roll upper bound, e.g. "100" -> 1..100
        try:
            n = int(s)
            return roll(n)
        except Exception as e:
            raise ValueError(f"Invalid dice expression: {expr!r}") from e

    # Split count and rest ("d20" => count="", rest="20")
    count_str, rest = s.split("d", 1)
    count = int(count_str) if count_str else 1

    # Modifier parsing
    mod = 0
    if "+" in rest:
        sides_str, mod_str = rest.split("+", 1)
        mod = int(mod_str)
    elif "-" in rest:
        sides_str, mod_str = rest.split("-", 1)
        mod = -int(mod_str)
    else:
        sides_str = rest

    sides = int(sides_str)
    if count < 1 or sides < 1:
        raise ValueError("Dice count and sides must be >= 1")

    total = sum(roll(sides) for _ in range(count)) + mod
    return total


# Convenience helpers for Brettventures balance tweaks -----------------

def nudge(base_roll: int, bonus: int, lo: int = 1, hi: int = 100) -> int:
    """
    Add a flat bonus then clamp into [lo, hi].
    Useful for turning stats (e.g., SMT+LCK) into small roll bumps.
    """
    return max(lo, min(hi, base_roll + bonus))


def chance_from_stat(stat: int, cap: int = 50) -> float:
    """
    Convert a stat to a probability in [0, 1] with a soft cap.
    Example: stat 0 -> 0.00, stat 25 -> 0.25, stat 80 -> 0.5 if cap=50.
    """
    return max(0.0, min(1.0, stat / float(cap)))
