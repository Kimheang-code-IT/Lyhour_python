"""Pavement Evaluation: traffic-class pavement structure and field-test targets.

The layer thicknesses and the FWD / LWD / B_Beam values below are project
placeholders so the page can auto-fill; replace them with the values from the
standard being applied. The material codes select the catalog hatch/color used
to draw each layer section.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.data.pavement_catalog import AC_HRA, CB2, DBM, GB3, GS2

TRAFFIC_CLASSES: tuple[str, ...] = ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8")

TRAFFIC_MSA_RANGES: dict[str, str] = {
    "T1": "< 0.3",
    "T2": "0.3 – 0.7",
    "T3": "0.7 – 1.5",
    "T4": "1.5 – 3.0",
    "T5": "3.0 – 6.0",
    "T6": "6.0 – 10",
    "T7": "10 – 17",
    "T8": "17 – 30",
}

# Fixed selected-subgrade thickness (mm) — same for every traffic class.
SELECTED_SUBGRADE_MM = 500.0


@dataclass(frozen=True)
class EvaluationLayerDef:
    key: str
    name: str
    cbr_note: str
    material: str  # catalog material code → color + hatch


# Top-to-bottom rows shown in the evaluation table.
LAYER_DEFS: tuple[EvaluationLayerDef, ...] = (
    EvaluationLayerDef("ac", "AC", "", AC_HRA),
    EvaluationLayerDef("base", "Base Course", "CBR >= 80%", CB2),
    EvaluationLayerDef("subbase", "Subbase", "CBR >= 30%", DBM),
    EvaluationLayerDef("selected_subgrade", "Selected Sub grade", "CBR >= 10%", GS2),
    EvaluationLayerDef("subgrade", "Sub grade (Embankment)", "CBR >= 2%", GB3),
)

# Placeholder design thickness (mm): traffic → {layer key: thickness}.
# The subgrade (embankment) is the formation and has no design thickness.
DESIGN_THICKNESS_MM: dict[str, dict[str, float]] = {
    "T1": {"ac": 40.0, "base": 125.0, "subbase": 150.0},
    "T2": {"ac": 40.0, "base": 125.0, "subbase": 150.0},
    "T3": {"ac": 40.0, "base": 150.0, "subbase": 150.0},
    "T4": {"ac": 40.0, "base": 150.0, "subbase": 175.0},
    "T5": {"ac": 50.0, "base": 175.0, "subbase": 175.0},
    "T6": {"ac": 50.0, "base": 175.0, "subbase": 200.0},
    "T7": {"ac": 50.0, "base": 200.0, "subbase": 200.0},
    "T8": {"ac": 60.0, "base": 200.0, "subbase": 225.0},
}

# Placeholder field-test targets: traffic → layer key → (FWD MPa, LWD MPa, B_Beam mm).
FIELD_TEST_VALUES: dict[str, dict[str, tuple[float, float, float]]] = {
    "T1": {
        "ac": (2600.0, 120.0, 0.35),
        "base": (180.0, 60.0, 0.60),
        "subbase": (100.0, 40.0, 0.85),
        "selected_subgrade": (60.0, 28.0, 1.05),
        "subgrade": (35.0, 18.0, 1.35),
    },
    "T2": {
        "ac": (2700.0, 130.0, 0.33),
        "base": (190.0, 65.0, 0.57),
        "subbase": (105.0, 42.0, 0.82),
        "selected_subgrade": (63.0, 30.0, 1.02),
        "subgrade": (38.0, 19.0, 1.30),
    },
    "T3": {
        "ac": (2800.0, 140.0, 0.31),
        "base": (200.0, 70.0, 0.54),
        "subbase": (110.0, 45.0, 0.79),
        "selected_subgrade": (66.0, 31.0, 0.98),
        "subgrade": (40.0, 20.0, 1.26),
    },
    "T4": {
        "ac": (2900.0, 150.0, 0.29),
        "base": (210.0, 75.0, 0.51),
        "subbase": (115.0, 48.0, 0.76),
        "selected_subgrade": (70.0, 33.0, 0.94),
        "subgrade": (43.0, 22.0, 1.21),
    },
    "T5": {
        "ac": (3000.0, 160.0, 0.27),
        "base": (220.0, 80.0, 0.48),
        "subbase": (120.0, 50.0, 0.73),
        "selected_subgrade": (74.0, 35.0, 0.90),
        "subgrade": (46.0, 24.0, 1.16),
    },
    "T6": {
        "ac": (3100.0, 165.0, 0.25),
        "base": (230.0, 85.0, 0.45),
        "subbase": (130.0, 55.0, 0.68),
        "selected_subgrade": (78.0, 38.0, 0.86),
        "subgrade": (49.0, 26.0, 1.11),
    },
    "T7": {
        "ac": (3250.0, 175.0, 0.22),
        "base": (245.0, 90.0, 0.41),
        "subbase": (140.0, 60.0, 0.62),
        "selected_subgrade": (84.0, 41.0, 0.80),
        "subgrade": (52.0, 28.0, 1.05),
    },
    "T8": {
        "ac": (3400.0, 180.0, 0.18),
        "base": (260.0, 95.0, 0.35),
        "subbase": (150.0, 65.0, 0.55),
        "selected_subgrade": (90.0, 45.0, 0.75),
        "subgrade": (55.0, 30.0, 1.00),
    },
}


@dataclass(frozen=True)
class EvaluationLayer:
    key: str
    name: str
    cbr_note: str
    material: str
    thickness_mm: float | None
    fwd_mpa: float | None
    lwd_mpa: float | None
    b_beam_mm: float | None


@dataclass(frozen=True)
class PavementEvaluation:
    traffic: str
    layers: tuple[EvaluationLayer, ...]

    @property
    def total_thickness_mm(self) -> float:
        return sum(layer.thickness_mm or 0.0 for layer in self.layers)


def compute_pavement_evaluation(traffic: str) -> PavementEvaluation:
    """Build the evaluation table rows for one traffic class."""
    thickness = DESIGN_THICKNESS_MM.get(traffic, {})
    field = FIELD_TEST_VALUES.get(traffic, {})

    layers: list[EvaluationLayer] = []
    for layer_def in LAYER_DEFS:
        if layer_def.key == "subgrade":
            thickness_mm: float | None = None
        elif layer_def.key == "selected_subgrade":
            thickness_mm = SELECTED_SUBGRADE_MM
        else:
            thickness_mm = thickness.get(layer_def.key)

        fwd, lwd, b_beam = field.get(layer_def.key, (None, None, None))
        layers.append(
            EvaluationLayer(
                key=layer_def.key,
                name=layer_def.name,
                cbr_note=layer_def.cbr_note,
                material=layer_def.material,
                thickness_mm=thickness_mm,
                fwd_mpa=fwd,
                lwd_mpa=lwd,
                b_beam_mm=b_beam,
            )
        )

    return PavementEvaluation(traffic=traffic, layers=tuple(layers))
