"""Pure logic: inputs -> floor area, volume, mass, optional cost."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class BuildingInputs:
    length_m: float
    width_m: float
    num_floors: int
    floor_height_m: float
    concrete_thickness_m: float
    concrete_density_kg_m3: float
    cost_per_m3: Optional[float] = None


@dataclass
class BuildingResults:
    floor_area_m2: float
    total_volume_m3: float
    estimated_mass_kg: float
    cost_estimate: Optional[float]


def compute(
    length_m: float,
    width_m: float,
    num_floors: int,
    floor_height_m: float,
    concrete_thickness_m: float,
    concrete_density_kg_m3: float,
    cost_per_m3: Optional[float] = None,
) -> BuildingResults:
    """Compute floor area, total volume, mass, and optional cost."""
    floor_area_m2 = length_m * width_m
    volume_per_floor = floor_area_m2 * concrete_thickness_m
    total_volume_m3 = volume_per_floor * num_floors
    estimated_mass_kg = total_volume_m3 * concrete_density_kg_m3
    cost_estimate = (total_volume_m3 * cost_per_m3) if cost_per_m3 is not None and cost_per_m3 > 0 else None
    return BuildingResults(
        floor_area_m2=floor_area_m2,
        total_volume_m3=total_volume_m3,
        estimated_mass_kg=estimated_mass_kg,
        cost_estimate=cost_estimate,
    )
