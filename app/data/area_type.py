"""Area type PCU factors for traffic analysis (Excel columns C–T)."""
from __future__ import annotations

from app.services.traffic_excel import VEHICLE_TYPE_COUNT

AREA_TYPE_OPTIONS: tuple[str, ...] = (
    "Rural Standard",
    "Urban Standard",
    "Roundabout Design",
    "Traffic Signal Design",
)

DEFAULT_AREA_TYPE = AREA_TYPE_OPTIONS[0]

# Vehicle types matching Excel columns C through T.
VEHICLE_TYPE_LABELS: tuple[str, ...] = (
    "Motor",
    "Tricycles",
    "Koyon",
    "Passenger Car",
    "Pick-up",
    "Max 15 Seats",
    "More than 15 Seats",
    "More than 24 Seats",
    "2 axles 4 tires",
    "2 axles 6 tires",
    "3 axles",
    "4 axles No-trailer",
    "4 axles Full-trailer",
    "4 axles Semi-trailer",
    "5 axles No-trailer",
    "5 axles Full-trailer",
    "5 axles Semi-trailer",
    "6 axles Semi-trailer",
)

_HEAVY_COLUMN_START = 10

# PCU factors per area type (one value per vehicle column C–T).
AREA_TYPE_PCU_FACTORS: dict[str, tuple[float, ...]] = {
    "Rural Standard": (
        0.4, 1.2, 1.2, 1.0, 1.0, 2.0, 2.0, 4.0, 2.5, 2.5,
        4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5,
    ),
    "Urban Standard": (
        0.4, 1.2, 1.2, 1.0, 1.0, 2.0, 2.0, 4.0, 2.5, 2.5,
        4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5,
    ),
    "Roundabout Design": (
        0.4, 1.0, 1.2, 1.0, 1.0, 2.0, 2.0, 3.75, 2.8, 2.8,
        4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0,
    ),
    "Traffic Signal Design": (
        0.33, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 3.5, 1.75, 1.75,
        3.75, 3.75, 3.75, 3.75, 3.75, 3.75, 3.75, 3.75,
    ),
}


def normalize_area_type(area_type: str | None) -> str:
    """Return a valid area type label, falling back to the default."""
    if area_type in AREA_TYPE_PCU_FACTORS:
        return area_type
    return DEFAULT_AREA_TYPE


def pcu_factors_for_area_type(area_type: str | None) -> list[float]:
    """PCU factors for one area type, length = VEHICLE_TYPE_COUNT."""
    key = normalize_area_type(area_type)
    factors = list(AREA_TYPE_PCU_FACTORS[key])
    if len(factors) < VEHICLE_TYPE_COUNT:
        factors.extend([factors[-1]] * (VEHICLE_TYPE_COUNT - len(factors)))
    return factors[:VEHICLE_TYPE_COUNT]


def heavy_pcu_factor_for_area_type(area_type: str | None) -> float:
    """Grouped heavy-vehicle PCU factor (columns L–T) for the selected area type."""
    factors = pcu_factors_for_area_type(area_type)
    if len(factors) > _HEAVY_COLUMN_START:
        return factors[_HEAVY_COLUMN_START]
    return factors[-1]
