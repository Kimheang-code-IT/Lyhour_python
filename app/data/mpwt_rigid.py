"""MPWT rigid pavement — input-driven analysis (thickness / damage check)."""
from __future__ import annotations

import math
from dataclasses import dataclass

RELIABILITY_OPTIONS = ("80%", "85%", "90%", "95%", "97.5%")
SHOULDER_OPTIONS = ("Yes", "No")
PAVEMENT_TYPE_OPTIONS = (
    "CRCP",
    "JRCP",
    "Undowelled PCP",
    "Undowelled SFCP",
)
SUBBASE_MATERIAL_OPTIONS = (
    "Granular",
    "Cement treated",
    "Lime treated",
    "Lean concrete",
)

_RELIABILITY_FACTOR = {
    "80%": 0.95,
    "85%": 0.97,
    "90%": 1.00,
    "95%": 1.05,
    "97.5%": 1.08,
}
_PAVEMENT_BASE_MM = {
    "CRCP": 180.0,
    "JRCP": 200.0,
    "Undowelled PCP": 220.0,
    "Undowelled SFCP": 210.0,
}
_MATERIAL_FACTOR = {
    "Granular": 1.00,
    "Cement treated": 1.12,
    "Lime treated": 1.08,
    "Lean concrete": 1.18,
}


@dataclass(frozen=True)
class MpwtRigidResult:
    effective_subgrade_strength: float
    trial_thickness_mm: float
    minimum_thickness_mm: float
    fatigue_damage_percent: float
    erosion_damage_percent: float
    design_pass: bool
    status_text: str


def effective_subgrade_strength(
    *,
    design_subgrade_strength: float,
    subbase_thickness_mm: float,
    subbase_material: str,
) -> float:
    """Composite effective support from subgrade + subbase."""
    base = max(0.0, float(design_subgrade_strength))
    mat = _MATERIAL_FACTOR.get(subbase_material, 1.0)
    h = max(0.0, float(subbase_thickness_mm))
    # Empirical support gain from subbase thickness (mm).
    gain = 1.0 + 0.15 * min(h, 300.0) / 150.0
    return base * mat * gain


def compute_mpwt_rigid(
    *,
    reliability: str,
    design_subgrade_strength: float,
    subbase_thickness_mm: float,
    subbase_material: str,
    effective_subgrade_strength_override: float | None,
    use_shoulder: str,
    pavement_type: str,
    concrete_strength: float,
    trial_thickness_mm: float,
) -> MpwtRigidResult:
    """Dynamic MPWT-style thickness / fatigue / erosion check."""
    ess = (
        float(effective_subgrade_strength_override)
        if effective_subgrade_strength_override is not None
        else effective_subgrade_strength(
            design_subgrade_strength=design_subgrade_strength,
            subbase_thickness_mm=subbase_thickness_mm,
            subbase_material=subbase_material,
        )
    )
    ess = max(ess, 0.01)
    rel = _RELIABILITY_FACTOR.get(reliability, 1.0)
    base_mm = _PAVEMENT_BASE_MM.get(pavement_type, 200.0)
    # Stronger support / concrete reduces required thickness.
    strength = max(float(concrete_strength), 0.01)
    min_mm = base_mm * rel * math.sqrt(4.0 / ess) * math.sqrt(4.5 / strength)
    min_mm = max(120.0, min_mm)

    trial = max(float(trial_thickness_mm), 1.0)
    shoulder_factor = 1.0 if use_shoulder == "Yes" else 1.15
    # Damage ratios — increase when trial is thin vs required.
    ratio = min_mm / trial
    fatigue = 100.0 * (ratio**3.2) * shoulder_factor * (4.5 / strength) ** 0.5
    erosion = 100.0 * (ratio**2.0) * (1.05 if use_shoulder != "Yes" else 0.85)

    design_pass = trial + 1e-9 >= min_mm and fatigue <= 100.0 and erosion <= 100.0
    return MpwtRigidResult(
        effective_subgrade_strength=ess,
        trial_thickness_mm=trial,
        minimum_thickness_mm=min_mm,
        fatigue_damage_percent=fatigue,
        erosion_damage_percent=erosion,
        design_pass=design_pass,
        status_text="PASS" if design_pass else "NOT PASS",
    )
