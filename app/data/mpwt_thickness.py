"""MPWT flexible pavement — layer thickness / structural number (AASHTO 1993).

Computes structural coefficients from layer moduli (not shown in UI), drainage
factors, required SN from the AASHTO equation, and SN provided by selected
layer thicknesses.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

MPA_TO_PSI = 145.03773773
CM_TO_INCH = 2.54

# Reliability R (%) → standard normal deviate ZR (AASHTO)
_ZR_BY_RELIABILITY: dict[int, float] = {
    50: 0.0,
    60: -0.253,
    70: -0.524,
    75: -0.674,
    80: -0.841,
    85: -1.037,
    90: -1.282,
    95: -1.645,
    99: -2.327,
}

MIN_THICKNESS_DEFAULTS = {
    "aashto_hma_cm": 8.9,
    "aashto_base_cm": 15.0,
    "japan_hma_cm": 8.9,
    "japan_base_cm": 20.0,
}


@dataclass(frozen=True)
class MpwtThicknessResult:
    a1: float
    a2: float
    a3: float
    sn1: float
    sn2: float
    sn3: float
    total_sn: float
    required_sn: float | None
    design_ok: bool | None
    zr: float


def reliability_to_zr(reliability_percent: float) -> float:
    """Interpolate ZR from the standard AASHTO reliability table."""
    r = float(reliability_percent)
    keys = sorted(_ZR_BY_RELIABILITY)
    if r <= keys[0]:
        return _ZR_BY_RELIABILITY[keys[0]]
    if r >= keys[-1]:
        return _ZR_BY_RELIABILITY[keys[-1]]
    for lo, hi in zip(keys, keys[1:]):
        if lo <= r <= hi:
            t = (r - lo) / (hi - lo)
            return _ZR_BY_RELIABILITY[lo] + t * (
                _ZR_BY_RELIABILITY[hi] - _ZR_BY_RELIABILITY[lo]
            )
    return _ZR_BY_RELIABILITY[75]


def structural_coefficient_a1(e1_mpa: float) -> float:
    """a1 = 0.17·ln(E1) − 0.9259, E1 in MPa."""
    e1 = max(float(e1_mpa), 1.0)
    return 0.17 * math.log(e1) - 0.9259


def structural_coefficient_a2(e2_mpa: float) -> float:
    """a2 = 0.249·log10(E2) − 0.977, E2 in psi."""
    e2_psi = max(float(e2_mpa) * MPA_TO_PSI, 1.0)
    return 0.249 * math.log10(e2_psi) - 0.977


def structural_coefficient_a3(e3_mpa: float) -> float:
    """a3 = 0.227·log10(E3) − 0.839, E3 in psi."""
    e3_psi = max(float(e3_mpa) * MPA_TO_PSI, 1.0)
    return 0.227 * math.log10(e3_psi) - 0.839


def log10_w18_predicted(
    sn: float,
    *,
    zr: float,
    s0: float,
    p0: float,
    pt: float,
    mr_psi: float,
) -> float:
    """AASHTO 1993 flexible pavement equation — log10(W18) for a trial SN."""
    sn_term = max(sn + 1.0, 1.01)
    delta_psi = max(p0 - pt, 1e-6)
    numer = math.log10(delta_psi / (4.2 - 1.5))
    denom = 0.4 + 1094.0 / (sn_term**5.19)
    mr = max(mr_psi, 1.0)
    return (
        zr * s0
        + 9.36 * math.log10(sn_term)
        - 0.20
        + numer / denom
        + 2.32 * math.log10(mr)
        - 8.07
    )


def required_structural_number(
    *,
    esal_million: float,
    reliability_percent: float,
    s0: float,
    p0: float,
    pt: float,
    mr_psi: float,
) -> float | None:
    """Solve AASHTO Eq. for SN given design ESALs (millions) and MR (psi)."""
    w18 = max(float(esal_million), 0.0) * 1_000_000.0
    if w18 <= 0 or mr_psi <= 0:
        return None

    target = math.log10(w18)
    zr = reliability_to_zr(reliability_percent)

    lo, hi = 0.1, 20.0
    f_lo = log10_w18_predicted(lo, zr=zr, s0=s0, p0=p0, pt=pt, mr_psi=mr_psi)
    f_hi = log10_w18_predicted(hi, zr=zr, s0=s0, p0=p0, pt=pt, mr_psi=mr_psi)

    # Expand upper bound if needed.
    while f_hi < target and hi < 40.0:
        hi *= 1.5
        f_hi = log10_w18_predicted(hi, zr=zr, s0=s0, p0=p0, pt=pt, mr_psi=mr_psi)

    if f_lo > target:
        return round(lo, 2)
    if f_hi < target:
        return round(hi, 2)

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = log10_w18_predicted(mid, zr=zr, s0=s0, p0=p0, pt=pt, mr_psi=mr_psi)
        if f_mid < target:
            lo = mid
        else:
            hi = mid
    return round(0.5 * (lo + hi), 2)


def compute_mpwt_thickness(
    *,
    a1: float,
    a2: float,
    a3: float,
    m2: float,
    m3: float,
    h1_cm: float,
    h2_cm: float,
    h3_cm: float,
    required_sn: float,
) -> MpwtThicknessResult:
    """Layer SN from selected thicknesses + required SN check."""
    a1_v = float(a1)
    a2_v = float(a2)
    a3_v = float(a3)

    h1_in = float(h1_cm) / CM_TO_INCH
    h2_in = float(h2_cm) / CM_TO_INCH
    h3_in = float(h3_cm) / CM_TO_INCH

    sn1 = a1_v * h1_in
    sn2 = a2_v * float(m2) * h2_in
    sn3 = a3_v * float(m3) * h3_in
    total = sn1 + sn2 + sn3

    required = float(required_sn)
    design_ok = total >= required

    return MpwtThicknessResult(
        a1=a1_v,
        a2=a2_v,
        a3=a3_v,
        sn1=sn1,
        sn2=sn2,
        sn3=sn3,
        total_sn=total,
        required_sn=required,
        design_ok=design_ok,
        zr=0.0,
    )
