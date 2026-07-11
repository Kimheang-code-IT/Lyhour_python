"""AASHTO effective roadbed soil resilient modulus (seasonal CBR)."""
from __future__ import annotations

import math
from dataclasses import dataclass

MR_CBR_FACTOR = 1500.0
UF_COEFFICIENT = 1.18e8
UF_MR_EXPONENT = -2.32

MONTH_LABELS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "June",
    "July",
    "Aug",
    "Sept.",
    "Oct.",
    "Nov.",
    "Dec.",
)


@dataclass(frozen=True)
class MonthlyResilientModulus:
    month: str
    cbr_percent: float
    cbr_effective_percent: float
    mr_psi: float
    relative_damage: float | None


@dataclass(frozen=True)
class EffectiveResilientModulusResult:
    months: tuple[MonthlyResilientModulus, ...]
    average_relative_damage: float | None
    effective_mr_psi: float | None


def cbr_effective_percent(cbr_percent: float) -> float:
    """Effective CBR equals the monthly input CBR in the reference spreadsheet."""
    return max(0.0, float(cbr_percent))


def resilient_modulus_psi(cbr_eff: float) -> float:
    """MR (psi) = CBR_eff × 1500."""
    return cbr_effective_percent(cbr_eff) * MR_CBR_FACTOR


def relative_damage_factor(mr_psi: float) -> float | None:
    """Relative damage uf = 1.18 × 10^8 × MR^(-2.32)."""
    mr = float(mr_psi)
    if mr <= 0:
        return None
    return UF_COEFFICIENT * (mr**UF_MR_EXPONENT)


def effective_mr_from_average_uf(average_uf: float) -> float | None:
    """Invert uf(MR) to obtain effective MR from average relative damage."""
    uf = float(average_uf)
    if uf <= 0:
        return None
    return (UF_COEFFICIENT / uf) ** (1.0 / abs(UF_MR_EXPONENT))


def compute_effective_resilient_modulus(
    monthly_cbr_percent: list[float],
) -> EffectiveResilientModulusResult:
    """Compute monthly MR/uf and effective roadbed resilient modulus."""
    values = list(monthly_cbr_percent[: len(MONTH_LABELS)])
    while len(values) < len(MONTH_LABELS):
        values.append(0.0)

    months: list[MonthlyResilientModulus] = []
    uf_values: list[float] = []

    for index, month in enumerate(MONTH_LABELS):
        cbr = max(0.0, float(values[index]))
        cbr_eff = cbr_effective_percent(cbr)
        mr = resilient_modulus_psi(cbr_eff)
        uf = relative_damage_factor(mr)
        if uf is not None:
            uf_values.append(uf)
        months.append(
            MonthlyResilientModulus(
                month=month,
                cbr_percent=cbr,
                cbr_effective_percent=cbr_eff,
                mr_psi=mr,
                relative_damage=uf,
            )
        )

    average_uf = sum(uf_values) / len(uf_values) if uf_values else None
    effective_mr = effective_mr_from_average_uf(average_uf) if average_uf is not None else None

    return EffectiveResilientModulusResult(
        months=tuple(months),
        average_relative_damage=average_uf,
        effective_mr_psi=effective_mr,
    )
