"""RSA encryption helpers and timing utilities for the complexity demo."""

from __future__ import annotations

import time
from dataclasses import dataclass

from sympy import randprime

# Exercise moduli (item b)
N1 = 2_469_247_531_693
N2 = 11_111_502_225_583
N3 = 44_444_222_221_411

EXERCISE_MODULI = {"n1": N1, "n2": N2, "n3": N3}

E = 65_537  # standard RSA public exponent
SECONDS_PER_YEAR = 3e7  # as stated in the exercise (~3 × 10^7)


def generate_rsa_modulus(
    p_digits: int = 10,
    q_digits: int = 11,
) -> tuple[int, int, int]:
    """Generate primes p, q with the given digit counts and return (p, q, n=pq)."""
    p_lo = 10 ** (p_digits - 1)
    p_hi = 10**p_digits - 1
    q_lo = 10 ** (q_digits - 1)
    q_hi = 10**q_digits - 1

    p = int(randprime(p_lo, p_hi + 1))
    q = int(randprime(q_lo, q_hi + 1))
    while q == p:
        q = int(randprime(q_lo, q_hi + 1))

    return p, q, p * q


def rsa_encrypt(m: int, e: int, n: int) -> int:
    """Compute c = m^e mod n (RSA encryption)."""
    return pow(m, e, n)


def encrypt_range(n: int, e: int, m_max: int) -> None:
    """
    Encrypt every plaintext m with 1 ≤ m < m_max.
    Results are intentionally discarded (not stored, not returned).
    """
    for m in range(1, m_max):
        rsa_encrypt(m, e, n)


@dataclass(frozen=True)
class TimingResult:
    n: int
    e: int
    m_max: int
    elapsed_seconds: float
    encryptions: int

    @property
    def rate(self) -> float:
        """Encryptions per second."""
        if self.elapsed_seconds <= 0:
            return float("inf")
        return self.encryptions / self.elapsed_seconds


def time_encrypt_range(
    n: int,
    e: int,
    m_max: int,
    progress_callback=None,
    progress_every: int = 100_000,
) -> TimingResult:
    """
    Time encryption of all m in [1, m_max).

    Optional progress_callback(done, total) for UI updates.
    """
    total = m_max - 1
    start = time.perf_counter()

    for m in range(1, m_max):
        rsa_encrypt(m, e, n)
        if progress_callback is not None and m % progress_every == 0:
            progress_callback(m, total)

    if progress_callback is not None:
        progress_callback(total, total)

    elapsed = time.perf_counter() - start
    return TimingResult(
        n=n,
        e=e,
        m_max=m_max,
        elapsed_seconds=elapsed,
        encryptions=total,
    )


def calibrate_m_max(
    n: int,
    e: int = E,
    candidates: tuple[int, ...] = (10**7, 10**8, 10**9),
    target_seconds: tuple[float, float] = (2.0, 60.0),
) -> int:
    """
    Pick m_max among 10^7 / 10^8 / 10^9 so the run is measurable but not endless.

    Samples a short batch, extrapolates, then chooses the largest candidate
    whose estimated duration stays under target_seconds[1], preferring at least
    target_seconds[0] when possible (exercise item c).
    """
    sample = 50_000
    sample = min(sample, candidates[0] - 1)
    result = time_encrypt_range(n, e, sample + 1)
    rate = result.rate

    lo, hi = target_seconds
    chosen = candidates[0]
    for cand in candidates:
        estimated = (cand - 1) / rate
        if estimated <= hi:
            chosen = cand
        if lo <= estimated <= hi:
            return cand
    return chosen


def estimate_full_space_time(
    measured: TimingResult,
    n: int | None = None,
) -> dict[str, float]:
    """
    Extrapolate measured timing to encrypt all m with 1 ≤ m < n (item d).

    Uses linear scaling: T(n) ≈ T(m_max) * (n - 1) / (m_max - 1).
    """
    target_n = n if n is not None else measured.n
    scale = (target_n - 1) / measured.encryptions
    seconds = measured.elapsed_seconds * scale
    years = seconds / SECONDS_PER_YEAR
    return {
        "seconds": seconds,
        "years": years,
        "target_n": float(target_n),
        "scale_factor": scale,
    }


def format_duration(seconds: float) -> str:
    """Human-readable duration for demos and reports."""
    if seconds < 1e-3:
        return f"{seconds * 1e6:.2f} µs"
    if seconds < 1:
        return f"{seconds * 1e3:.2f} ms"
    if seconds < 60:
        return f"{seconds:.3f} s"
    if seconds < 3600:
        return f"{seconds / 60:.2f} min"
    if seconds < 86_400:
        return f"{seconds / 3600:.2f} h"
    if seconds < SECONDS_PER_YEAR:
        return f"{seconds / 86_400:.2f} days"
    years = seconds / SECONDS_PER_YEAR
    if years < 1_000:
        return f"{years:.2f} years"
    if years < 1e6:
        return f"{years / 1e3:.2f} × 10³ years"
    if years < 1e9:
        return f"{years / 1e6:.2f} × 10⁶ years"
    return f"{years:.3e} years"


def digit_count(x: int) -> int:
    return len(str(abs(x)))
