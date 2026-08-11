"""AASHTO 1993 rigid pavement thickness design (from Thickness Design ASSHTO93)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.data.aashto_resilient_modulus import MONTH_LABELS

MPA_TO_PSI = 145.038
CM_TO_INCH = 2.54
PCI_TO_MPA_PER_M = 0.271

MR_CBR_FACTOR = 1500.0

_ZR_BY_RELIABILITY: dict[float, float] = {
    50: 0.0,
    60: -0.253,
    70: -0.524,
    75: -0.674,
    80: -0.841,
    85: -1.037,
    90: -1.282,
    95: -1.645,
    99: -2.327,
    99.9: -3.09,
}


@dataclass(frozen=True)
class RigidMonthlyRow:
    month: str
    cbr_percent: float
    cbr_effective_percent: float
    mr_psi: float
    k_eq_pci: float
    relative_damage_ur: float | None


@dataclass(frozen=True)
class AashtoRigidResult:
    months: tuple[RigidMonthlyRow, ...]
    average_ur: float | None
    effective_k_pci: float | None
    effective_k_mpa_per_m: float | None
    corrected_k_pci: float | None
    dcal_inch: float | None
    dcal_cm: float | None
    difference_ratio: float | None
    verification_ok: bool | None
    final_thickness_cm: int | None
    zr: float
    base_subbase_factor: float


def reliability_to_zr(reliability_percent: float) -> float:
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
    return _ZR_BY_RELIABILITY[80]


def cbr_effective_percent(
    *,
    cbr_month: float,
    cbr_selected: float,
    h4_cm: float,
) -> float:
    """Workbook: ((h4·CBR_sel^(1/3)+(100−h4)·CBR_m^(1/3))/100)^3."""
    h4 = max(0.0, min(100.0, float(h4_cm)))
    cbr_m = max(0.0, float(cbr_month))
    cbr_s = max(0.0, float(cbr_selected))
    return ((h4 * (cbr_s ** (1.0 / 3.0)) + (100.0 - h4) * (cbr_m ** (1.0 / 3.0))) / 100.0) ** 3


def resilient_modulus_psi(cbr_eff: float) -> float:
    """MR (psi) = CBR_eff × 1500 (AASHTO roadbed correlation)."""
    return max(0.0, float(cbr_eff)) * MR_CBR_FACTOR


def base_subbase_composite_factor(
    *,
    e2_mpa: float,
    e3_mpa: float,
    h2_cm: float,
    h3_cm: float,
) -> float:
    """Aid-sheet regression factors E152…E155 product (E156)."""
    e2_psi = max(1.0, float(e2_mpa) * MPA_TO_PSI)
    e3_psi = max(1.0, float(e3_mpa) * MPA_TO_PSI)
    h2_in = max(0.0, float(h2_cm) / CM_TO_INCH)
    h3_in = max(0.0, float(h3_cm) / CM_TO_INCH)
    f_e2 = 0.9993 * (e2_psi / 30000.0) ** 0.1655
    f_e3 = 0.9994 * (e3_psi / 20000.0) ** 0.2084
    f_h2 = 0.2015 * (h2_in / 8.0) + 0.7993
    f_h3 = 0.197 * (h3_in / 8.0) + 0.8074
    return f_e2 * f_e3 * f_h2 * f_h3


def k_eq_pci(mr_psi: float, composite_factor: float) -> float:
    """k_eq = (0.9994·(MR/7500)^0.6207)·423·factor."""
    mr = max(1.0, float(mr_psi))
    return (0.9994 * (mr / 7500.0) ** 0.6207) * 423.0 * float(composite_factor)


def relative_damage_ur(*, das_cm: float, k_eq: float) -> float | None:
    """ur = ((Das/2.54)^0.75 − 0.39·k_eq^0.25)^3.42."""
    das_in = float(das_cm) / CM_TO_INCH
    if das_in <= 0 or k_eq <= 0:
        return None
    inner = das_in**0.75 - 0.39 * (float(k_eq) ** 0.25)
    if inner <= 0:
        return None
    return inner**3.42


def effective_k_from_average_ur(*, das_cm: float, average_ur: float) -> float | None:
    """Invert ur(k) for effective modulus of subgrade reaction (pci)."""
    das_in = float(das_cm) / CM_TO_INCH
    ur = float(average_ur)
    if das_in <= 0 or ur <= 0:
        return None
    try:
        return 10.0 ** (
            math.log10((das_in**0.75 - 10.0 ** (math.log10(ur) / 3.42)) / 0.39) / 0.25
        )
    except (ValueError, ZeroDivisionError):
        return None


def correct_k_for_loss_of_support(k_pci: float, ls: int) -> float:
    """Workbook LS correction on effective k."""
    k = max(0.0, float(k_pci))
    level = int(ls)
    if level <= 0:
        return k
    if level == 1:
        return 0.4953 * (k**0.9214)
    if level == 2:
        return 0.6704 * (k**0.6669)
    return 0.6761 * (k**0.5231)


def aashto_rigid_log_w18_residual(
    d_inch: float,
    *,
    w18: float,
    zr: float,
    s0: float,
    p0: float,
    pt: float,
    sc_psi: float,
    ec_psi: float,
    j: float,
    cd: float,
    k_pci: float,
) -> float:
    """Aid-sheet F(D): positive ⇒ thickness too thin."""
    d = max(d_inch, 0.5)
    k = max(float(k_pci), 1.0)
    ec = max(float(ec_psi), 1.0)
    term1 = (
        math.log10(max(w18, 1.0))
        - zr * s0
        - 7.35 * math.log10(d + 1.0)
        + 0.06
    )
    psi = max(p0 - pt, 1e-6)
    term2 = math.log10(psi / (4.5 - 1.5)) / (
        1.0 + 1.624e7 / ((d + 1.0) ** 8.46)
    )
    num = sc_psi * cd * (d**0.75 - 1.132)
    den = 215.63 * j * (d**0.75 - 18.42 / ((ec / k) ** 0.25))
    if num <= 0 or den <= 0:
        return 1e6
    term3 = (4.22 - 0.32 * pt) * math.log10(num / den)
    return term1 - term2 - term3


def solve_required_thickness_inch(
    *,
    esal_million: float,
    reliability_percent: float,
    s0: float,
    p0: float,
    pt: float,
    sc_mpa: float,
    ec_mpa: float,
    j: float,
    cd: float,
    k_pci: float,
) -> float | None:
    """Bisection solver for D (inches), matching Aid-sheet iterations."""
    if esal_million <= 0 or k_pci <= 0 or sc_mpa <= 0 or ec_mpa <= 0:
        return None
    w18 = float(esal_million) * 1_000_000.0
    zr = reliability_to_zr(reliability_percent)
    sc_psi = float(sc_mpa) * MPA_TO_PSI
    ec_psi = float(ec_mpa) * MPA_TO_PSI
    lo, hi = 2.0, 20.0
    f_hi = aashto_rigid_log_w18_residual(
        hi,
        w18=w18,
        zr=zr,
        s0=s0,
        p0=p0,
        pt=pt,
        sc_psi=sc_psi,
        ec_psi=ec_psi,
        j=j,
        cd=cd,
        k_pci=k_pci,
    )
    while f_hi > 0 and hi < 40.0:
        hi *= 1.25
        f_hi = aashto_rigid_log_w18_residual(
            hi,
            w18=w18,
            zr=zr,
            s0=s0,
            p0=p0,
            pt=pt,
            sc_psi=sc_psi,
            ec_psi=ec_psi,
            j=j,
            cd=cd,
            k_pci=k_pci,
        )
    mid = 0.5 * (lo + hi)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        f_mid = aashto_rigid_log_w18_residual(
            mid,
            w18=w18,
            zr=zr,
            s0=s0,
            p0=p0,
            pt=pt,
            sc_psi=sc_psi,
            ec_psi=ec_psi,
            j=j,
            cd=cd,
            k_pci=k_pci,
        )
        if f_mid > 0:
            lo = mid
        else:
            hi = mid
    return mid


def round_up_thickness_cm(dcal_cm: float) -> int:
    """Practical whole-cm design thickness (round up)."""
    if dcal_cm <= 0:
        return 0
    return int(math.ceil(dcal_cm - 1e-9))


def compute_aashto_rigid(
    *,
    esal_million: float,
    pt: float,
    p0: float,
    s0: float,
    reliability_percent: float,
    sc_mpa: float,
    j: float,
    cd: float,
    ls: int,
    das_cm: float,
    ec_mpa: float,
    e2_mpa: float,
    h2_cm: float,
    e3_mpa: float,
    h3_cm: float,
    cbr_selected: float,
    h4_cm: float,
    monthly_cbr_percent: list[float],
) -> AashtoRigidResult:
    """Full AASHTO 1993 rigid thickness workflow from the Excel workbook."""
    factor = base_subbase_composite_factor(
        e2_mpa=e2_mpa, e3_mpa=e3_mpa, h2_cm=h2_cm, h3_cm=h3_cm
    )
    values = list(monthly_cbr_percent[: len(MONTH_LABELS)])
    while len(values) < len(MONTH_LABELS):
        values.append(0.0)

    months: list[RigidMonthlyRow] = []
    ur_values: list[float] = []
    for index, month in enumerate(MONTH_LABELS):
        cbr = max(0.0, float(values[index]))
        cbr_eff = cbr_effective_percent(
            cbr_month=cbr, cbr_selected=cbr_selected, h4_cm=h4_cm
        )
        mr = resilient_modulus_psi(cbr_eff)
        keq = k_eq_pci(mr, factor)
        ur = relative_damage_ur(das_cm=das_cm, k_eq=keq)
        if ur is not None:
            ur_values.append(ur)
        months.append(
            RigidMonthlyRow(
                month=month,
                cbr_percent=cbr,
                cbr_effective_percent=cbr_eff,
                mr_psi=mr,
                k_eq_pci=keq,
                relative_damage_ur=ur,
            )
        )

    average_ur = sum(ur_values) / len(ur_values) if ur_values else None
    k_eff = (
        effective_k_from_average_ur(das_cm=das_cm, average_ur=average_ur)
        if average_ur is not None
        else None
    )
    k_corr = correct_k_for_loss_of_support(k_eff, ls) if k_eff is not None else None

    dcal_in = None
    if k_corr is not None:
        dcal_in = solve_required_thickness_inch(
            esal_million=esal_million,
            reliability_percent=reliability_percent,
            s0=s0,
            p0=p0,
            pt=pt,
            sc_mpa=sc_mpa,
            ec_mpa=ec_mpa,
            j=j,
            cd=cd,
            k_pci=k_corr,
        )
    dcal_cm = None if dcal_in is None else dcal_in * CM_TO_INCH
    difference = None
    ok = None
    final_cm = None
    if dcal_cm is not None and dcal_cm > 0:
        difference = abs((dcal_cm - float(das_cm)) / dcal_cm)
        ok = difference < 0.05
        final_cm = round_up_thickness_cm(dcal_cm)

    return AashtoRigidResult(
        months=tuple(months),
        average_ur=average_ur,
        effective_k_pci=k_eff,
        effective_k_mpa_per_m=None if k_eff is None else k_eff * PCI_TO_MPA_PER_M,
        corrected_k_pci=k_corr,
        dcal_inch=dcal_in,
        dcal_cm=dcal_cm,
        difference_ratio=difference,
        verification_ok=ok,
        final_thickness_cm=final_cm,
        zr=reliability_to_zr(reliability_percent),
        base_subbase_factor=factor,
    )
