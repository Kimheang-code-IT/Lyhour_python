"""Road classification (Rural R / Urban U) from projected AADT."""
from __future__ import annotations

from app.core.result_description_html import (
    result_highlight_style,
    wrap_result_description_lines,
)

# AADT bands from the reference table (columns left to right).
# 3,001 – 10,000 → R4 / U4
# > 10,000 → R5 / U5
_AADT_BANDS: tuple[tuple[int, int | None, str, str], ...] = (
    (10_001, None, "R5", "U5"),      # > 10,000
    (3_001, 10_000, "R4", "U4"),     # 3,001 – 10,000
    (1_001, 3_000, "R3", "U3"),      # 1,001 – 3,000
    (150, 1_000, "R2", "U2"),        # 150 – 1,000
    (0, 149, "R1", "U1"),            # < 150
)


def rural_class_from_aadt(aadt: int) -> str:
    """Rural road class (R1–R5) from projected AADT."""
    return _classify_volume(aadt)[0]


def urban_class_from_pcu(pcu: int) -> str:
    """Urban road class (U1–U5) from projected PCU."""
    return _classify_volume(pcu)[1]


def urban_class_from_aadt(aadt: int) -> str:
    """Urban road class (U1–U5) from projected AADT."""
    return _classify_volume(aadt)[1]


def _classify_volume(volume: int) -> tuple[str, str]:
    value = max(0, int(volume))
    for minimum, maximum, rural, urban in _AADT_BANDS:
        if value < minimum:
            continue
        if maximum is not None and value > maximum:
            continue
        return rural, urban
    return "R1", "U1"


def road_classification_code(aadt: int, pcu: int | None = None) -> str:
    """
    Return combined label such as R5/U5.

    Rural (R) uses projected AADT. Urban (U) uses projected PCU.
    Example: AADT 5,000 and PCU 5,000 in the 3,001–10,000 band → R4/U4.
    """
    rural = rural_class_from_aadt(aadt)
    urban = urban_class_from_pcu(pcu) if pcu and pcu > 0 else urban_class_from_aadt(aadt)
    return f"{rural}/{urban}"


def build_road_classification_text(
    design_year: str,
    projected_aadt: int | None,
    projected_pcu: int | None,
) -> str:
    """HTML description for the Road Classification tab."""
    placeholder = "____"
    year = design_year.strip() if design_year else placeholder
    aadt_text = f"{projected_aadt:,}" if projected_aadt else placeholder
    pcu_text = f"{projected_pcu:,}" if projected_pcu else placeholder

    highlight = result_highlight_style()
    lines = [
        f'- The design year is <span style="{highlight}">{year}</span>',
        (
            f'- So the projected AADT in <span style="{highlight}">{year}</span>&nbsp;&nbsp;'
            f'is <span style="{highlight}">{aadt_text}</span> and projected PCU in '
            f'<span style="{highlight}">{pcu_text}</span>'
        ),
    ]

    if projected_aadt and projected_aadt > 0:
        code = road_classification_code(projected_aadt, projected_pcu)
        lines.append(f"- So, Road classification is {code}")

    return wrap_result_description_lines(lines)
