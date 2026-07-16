"""Flexible pavement catalog tables (foundation × traffic → layer stack).

Tables follow the Foundation Class / Traffic Class catalogs used on Catalog/Analysis.
Each design is a top-to-bottom list of layers: (material_code, thickness_mm).
DBST surface is stored with thickness 0 (drawn as a thin seal band on the chart).
"""
from __future__ import annotations

from dataclasses import dataclass


# --- Material codes ---------------------------------------------------------

DBST = "DBST"
AC_HRA = "AC/HRA"
DBM = "DBM"
GB1_BSM = "GB1/BSM"
GB2 = "GB2"
GB3 = "GB3"
GS2 = "GS2"
CB1 = "CB1"
CB2 = "CB2"

MATERIAL_LABELS: dict[str, str] = {
    DBST: "Double Bituminous Surface Treatment (DBST)",
    AC_HRA: "Asphalt Concrete / Hot Rolled Asphalt (AC/HRA)",
    DBM: "Dense Bitumen Macadam (DBM)",
    GB1_BSM: "Granular Base 1 / Bitumen Stabilised Material (GB1/BSM)",
    GB2: "Granular Base 2 (GB2)",
    GB3: "Granular Base 3 (GB3)",
    GS2: "Granular Subbase 2 (GS2)",
    CB1: "Hydraulically Bound Material (CB1)",
    CB2: "Hydraulically Modified Material (CB2)",
}

# Light engineering-drawing fills (hatches carry the material identity).
MATERIAL_COLORS: dict[str, str] = {
    DBST: "#111111",
    AC_HRA: "#1a1a1a",
    DBM: "#b0b0b0",
    GB1_BSM: "#e8e8e8",
    GB2: "#efefef",
    GB3: "#e6d5bc",
    GS2: "#f0d0c4",
    CB1: "#f5e28a",
    CB2: "#f0dcc0",
}

# Matplotlib hatch patterns matching catalog cross-section drawings.
MATERIAL_HATCHES: dict[str, str] = {
    DBST: "",
    AC_HRA: "",
    DBM: "xx",
    GB1_BSM: "..",
    GB2: "..",
    GB3: "..",
    GS2: "///",
    CB1: "|||",
    CB2: "---",
}

TRAFFIC_MSA_RANGES: dict[str, str] = {
    "T1": "< 0.3",
    "T2": "0.3 – 0.7",
    "T3": "0.7 – 1.5",
    "T4": "1.5 – 3.0",
    "T5": "3.0 – 6.0",
    "T6": "6.0 – 10",
    "T7": "10 – 17",
    "T8": "17 – 30",
    "T9": "30 – 50",
    "T10": "50 – 80",
}

FOUNDATION_OPTIONS = ("F1 (S3)", "F2 (S4)", "F3 (S5)", "F4 (S6)")

FOUNDATION_CODES: dict[str, str] = {
    "F1 (S3)": "F1",
    "F2 (S4)": "F2",
    "F3 (S5)": "F3",
    "F4 (S6)": "F4",
    "F1": "F1",
    "F2": "F2",
    "F3": "F3",
    "F4": "F4",
}

# Select 2 = catalog structure family (filtered by seal type).
CATALOG_DBST_GRANULAR = "DBST - Granular (GB + GS2)"
CATALOG_DBST_GB_CB = "DBST - Granular + Cemented (GB + CB)"
CATALOG_DBST_CB_GS = "DBST - Cemented (CB + GS2)"
CATALOG_AC_GRANULAR = "AC - Granular (GB + GS2)"
CATALOG_AC_DBM_GS = "AC - DBM + Granular (DBM + GB + GS2)"
CATALOG_AC_GB_CB = "AC - Granular + Cemented (GB + CB)"
CATALOG_AC_DBM_CB = "AC - DBM + Cemented (DBM + GB + CB)"

CATALOG_OPTIONS_BY_SEAL: dict[str, tuple[str, ...]] = {
    "DBST": (CATALOG_DBST_GRANULAR, CATALOG_DBST_GB_CB, CATALOG_DBST_CB_GS),
    "AC": (CATALOG_AC_GRANULAR, CATALOG_AC_DBM_GS, CATALOG_AC_GB_CB, CATALOG_AC_DBM_CB),
}


@dataclass(frozen=True)
class CatalogLayer:
    material: str
    thickness_mm: float  # 0 = thin seal (DBST visual band)


@dataclass(frozen=True)
class PavementCatalogDesign:
    seal_type: str
    catalog_name: str
    traffic: str
    foundation: str
    layers: tuple[CatalogLayer, ...]

    @property
    def total_thickness_mm(self) -> float:
        return sum(layer.thickness_mm for layer in self.layers)

    @property
    def layer_summary(self) -> str:
        parts: list[str] = []
        for layer in self.layers:
            if layer.thickness_mm <= 0:
                parts.append(layer.material)
            else:
                parts.append(f"{layer.material} {layer.thickness_mm:.0f} mm")
        return " / ".join(parts)


def _L(material: str, thickness_mm: float) -> CatalogLayer:
    return CatalogLayer(material=material, thickness_mm=float(thickness_mm))


def _stack(*layers: CatalogLayer) -> tuple[CatalogLayer, ...]:
    return layers


def _dbst(*below: CatalogLayer) -> tuple[CatalogLayer, ...]:
    return (_L(DBST, 0.0), *below)


def _ac(thickness: float, *below: CatalogLayer) -> tuple[CatalogLayer, ...]:
    return (_L(AC_HRA, thickness), *below)


# ---------------------------------------------------------------------------
# Catalog 1 — DBST + GB + GS2 (T1–T6)
# ---------------------------------------------------------------------------
_CATALOG_DBST_GRANULAR: dict[str, dict[str, tuple[CatalogLayer, ...]]] = {
    "F1": {
        "T1": _dbst(_L(GB3, 150), _L(GS2, 175)),
        "T2": _dbst(_L(GB3, 150), _L(GS2, 175)),
        "T3": _dbst(_L(GB3, 175), _L(GS2, 175)),
        "T4": _dbst(_L(GB2, 200), _L(GS2, 200)),
        "T5": _dbst(_L(GB1_BSM, 200), _L(GS2, 250)),
        "T6": _dbst(_L(GB1_BSM, 225), _L(GS2, 250)),
    },
    "F2": {
        "T1": _dbst(_L(GB3, 150), _L(GS2, 150)),
        "T2": _dbst(_L(GB3, 150), _L(GS2, 150)),
        "T3": _dbst(_L(GB3, 175), _L(GS2, 150)),
        "T4": _dbst(_L(GB2, 200), _L(GS2, 175)),
        "T5": _dbst(_L(GB1_BSM, 200), _L(GS2, 225)),
        "T6": _dbst(_L(GB1_BSM, 225), _L(GS2, 225)),
    },
    "F3": {
        "T1": _dbst(_L(GB3, 125), _L(GS2, 100)),
        "T2": _dbst(_L(GB3, 125), _L(GS2, 100)),
        "T3": _dbst(_L(GB3, 150), _L(GS2, 100)),
        "T4": _dbst(_L(GB2, 175), _L(GS2, 100)),
        "T5": _dbst(_L(GB1_BSM, 200), _L(GS2, 100)),
        "T6": _dbst(_L(GB1_BSM, 200), _L(GS2, 150)),
    },
    "F4": {
        "T1": _dbst(_L(GB3, 150)),
        "T2": _dbst(_L(GB3, 150)),
        "T3": _dbst(_L(GB3, 175)),
        "T4": _dbst(_L(GB2, 175)),
        "T5": _dbst(_L(GB1_BSM, 200)),
        "T6": _dbst(_L(GB1_BSM, 225)),
    },
}

# ---------------------------------------------------------------------------
# Catalog 2 — DBST + GB + CB1/CB2 (T1–T7)
# ---------------------------------------------------------------------------
_CATALOG_DBST_GB_CB: dict[str, dict[str, tuple[CatalogLayer, ...]]] = {
    "F1": {
        "T1": _dbst(_L(GB3, 125), _L(CB2, 150)),
        "T2": _dbst(_L(GB3, 125), _L(CB2, 150)),
        "T3": _dbst(_L(GB3, 150), _L(CB2, 150)),
        "T4": _dbst(_L(GB2, 150), _L(CB2, 175)),
        "T5": _dbst(_L(GB1_BSM, 150), _L(CB2, 225)),
        "T6": _dbst(_L(GB1_BSM, 150), _L(CB1, 125), _L(CB2, 175)),
        "T7": _dbst(_L(GB1_BSM, 150), _L(CB1, 125), _L(CB2, 200)),
    },
    "F2": {
        "T1": _dbst(_L(GB3, 125), _L(CB2, 175)),
        "T2": _dbst(_L(GB3, 125), _L(CB2, 175)),
        "T3": _dbst(_L(GB3, 150), _L(CB2, 175)),
        "T4": _dbst(_L(GB2, 150), _L(CB2, 200)),
        "T5": _dbst(_L(GB1_BSM, 150), _L(CB2, 200)),
        "T6": _dbst(_L(GB1_BSM, 150), _L(CB1, 125), _L(CB2, 125)),
        "T7": _dbst(_L(GB1_BSM, 150), _L(CB1, 125), _L(CB2, 175)),
    },
    "F3": {
        "T1": _dbst(_L(GB3, 125), _L(CB2, 125)),
        "T2": _dbst(_L(GB3, 125), _L(CB2, 125)),
        "T3": _dbst(_L(GB3, 150), _L(CB2, 125)),
        "T4": _dbst(_L(GB2, 150), _L(CB2, 150)),
        "T5": _dbst(_L(GB1_BSM, 150), _L(CB2, 175)),
        "T6": _dbst(_L(GB1_BSM, 150), _L(CB1, 200)),
        "T7": _dbst(_L(GB1_BSM, 150), _L(CB1, 250)),
    },
    "F4": {
        "T1": _dbst(_L(GB3, 150)),
        "T2": _dbst(_L(GB3, 150)),
        "T3": _dbst(_L(GB3, 175)),
        "T4": _dbst(_L(GB2, 175)),
        "T5": _dbst(_L(GB1_BSM, 200)),
        "T6": _dbst(_L(GB1_BSM, 175), _L(CB1, 150)),
        "T7": _dbst(_L(GB1_BSM, 175), _L(CB1, 175)),
    },
}

# ---------------------------------------------------------------------------
# Catalog 3 — DBST + CB1/CB2 + GS2 (T1–T7)
# ---------------------------------------------------------------------------
_CATALOG_DBST_CB_GS: dict[str, dict[str, tuple[CatalogLayer, ...]]] = {
    "F1": {
        "T1": _dbst(_L(CB1, 150), _L(GS2, 225)),
        "T2": _dbst(_L(CB1, 150), _L(GS2, 225)),
        "T3": _dbst(_L(CB1, 175), _L(GS2, 225)),
        "T4": _dbst(_L(CB1, 175), _L(GS2, 250)),
        "T5": _dbst(_L(CB1, 200), _L(GS2, 300)),
        "T6": _dbst(_L(CB1, 200), _L(CB2, 125), _L(GS2, 200)),
        "T7": _dbst(_L(CB1, 225), _L(CB2, 150), _L(GS2, 200)),
    },
    "F2": {
        "T1": _dbst(_L(CB1, 150), _L(GS2, 175)),
        "T2": _dbst(_L(CB1, 150), _L(GS2, 175)),
        "T3": _dbst(_L(CB1, 175), _L(GS2, 200)),
        "T4": _dbst(_L(CB1, 175), _L(GS2, 200)),
        "T5": _dbst(_L(CB1, 200), _L(GS2, 250)),
        "T6": _dbst(_L(CB1, 200), _L(GS2, 300)),
        "T7": _dbst(_L(CB1, 225), _L(GS2, 300)),
    },
    "F3": {
        "T1": _dbst(_L(CB1, 150), _L(GS2, 100)),
        "T2": _dbst(_L(CB1, 150), _L(GS2, 100)),
        "T3": _dbst(_L(CB1, 175), _L(GS2, 100)),
        "T4": _dbst(_L(CB1, 175), _L(GS2, 150)),
        "T5": _dbst(_L(CB1, 200), _L(GS2, 175)),
        "T6": _dbst(_L(CB1, 200), _L(GS2, 200)),
        "T7": _dbst(_L(CB1, 225), _L(GS2, 200)),
    },
    "F4": {
        "T1": _dbst(_L(CB1, 150)),
        "T2": _dbst(_L(CB1, 150)),
        "T3": _dbst(_L(CB1, 175)),
        "T4": _dbst(_L(CB1, 200)),
        "T5": _dbst(_L(CB1, 225)),
        "T6": _dbst(_L(CB1, 250)),
        "T7": _dbst(_L(CB1, 275)),
    },
}

# ---------------------------------------------------------------------------
# Catalog 4 — AC + GB + GS2 (T3–T6)
# ---------------------------------------------------------------------------
_CATALOG_AC_GRANULAR: dict[str, dict[str, tuple[CatalogLayer, ...]]] = {
    "F1": {
        "T3": _ac(40, _L(GB3, 175), _L(GS2, 225)),
        "T4": _ac(40, _L(GB2, 175), _L(GS2, 275)),
        "T5": _ac(40, _L(GB1_BSM, 175), _L(GS2, 325)),
        "T6": _ac(50, _L(GB1_BSM, 200), _L(GS2, 350)),
    },
    "F2": {
        "T3": _ac(40, _L(GB3, 175), _L(GS2, 150)),
        "T4": _ac(40, _L(GB2, 175), _L(GS2, 175)),
        "T5": _ac(40, _L(GB1_BSM, 175), _L(GS2, 225)),
        "T6": _ac(50, _L(GB1_BSM, 200), _L(GS2, 250)),
    },
    "F3": {
        "T3": _ac(40, _L(GB3, 150), _L(GS2, 100)),
        "T4": _ac(40, _L(GB2, 150), _L(GS2, 125)),
        "T5": _ac(40, _L(GB2, 150), _L(GS2, 150)),
        "T6": _ac(50, _L(GB2, 175), _L(GS2, 175)),
    },
    "F4": {
        "T3": _ac(40, _L(GB3, 150)),
        "T4": _ac(40, _L(GB2, 175)),
        "T5": _ac(40, _L(GB1_BSM, 200)),
        "T6": _ac(50, _L(GB1_BSM, 225)),
    },
}

# ---------------------------------------------------------------------------
# Catalog 5 — AC + DBM + GB1 + GS2 (T6–T9)
# ---------------------------------------------------------------------------
_CATALOG_AC_DBM_GS: dict[str, dict[str, tuple[CatalogLayer, ...]]] = {
    "F1": {
        "T6": _ac(40, _L(DBM, 60), _L(GB1_BSM, 200), _L(GS2, 225)),
        "T7": _ac(50, _L(DBM, 75), _L(GB1_BSM, 200), _L(GS2, 250)),
        "T8": _ac(50, _L(DBM, 100), _L(GB1_BSM, 200), _L(GS2, 275)),
        "T9": _ac(50, _L(DBM, 125), _L(GB1_BSM, 200), _L(GS2, 300)),
    },
    "F2": {
        "T6": _ac(40, _L(DBM, 60), _L(GB1_BSM, 200), _L(GS2, 175)),
        "T7": _ac(50, _L(DBM, 75), _L(GB1_BSM, 200), _L(GS2, 200)),
        "T8": _ac(50, _L(DBM, 100), _L(GB1_BSM, 200), _L(GS2, 225)),
        "T9": _ac(50, _L(DBM, 125), _L(GB1_BSM, 200), _L(GS2, 250)),
    },
    "F3": {
        "T6": _ac(40, _L(DBM, 60), _L(GB1_BSM, 150), _L(GS2, 150)),
        "T7": _ac(50, _L(DBM, 75), _L(GB1_BSM, 175), _L(GS2, 150)),
        "T8": _ac(50, _L(DBM, 100), _L(GB1_BSM, 200), _L(GS2, 150)),
        "T9": _ac(50, _L(DBM, 125), _L(GB1_BSM, 225), _L(GS2, 150)),
    },
    "F4": {
        "T6": _ac(40, _L(DBM, 60), _L(GB1_BSM, 200)),
        "T7": _ac(50, _L(DBM, 75), _L(GB1_BSM, 225)),
        "T8": _ac(50, _L(DBM, 100), _L(GB1_BSM, 250)),
        "T9": _ac(50, _L(DBM, 125), _L(GB1_BSM, 275)),
    },
}

# ---------------------------------------------------------------------------
# Catalog 6 — AC + GB1 + CB1 (T6–T10; T10 adds DBM)
# ---------------------------------------------------------------------------
_CATALOG_AC_GB_CB: dict[str, dict[str, tuple[CatalogLayer, ...]]] = {
    "F1": {
        "T6": _ac(50, _L(GB1_BSM, 150), _L(CB1, 275)),
        "T7": _ac(50, _L(GB1_BSM, 150), _L(CB1, 300)),
        "T8": _ac(50, _L(GB1_BSM, 175), _L(CB1, 300)),
        "T9": _ac(75, _L(GB1_BSM, 175), _L(CB1, 300)),
        "T10": _ac(40, _L(DBM, 60), _L(GB1_BSM, 175), _L(CB1, 300)),
    },
    "F2": {
        "T6": _ac(50, _L(GB1_BSM, 150), _L(CB1, 200)),
        "T7": _ac(50, _L(GB1_BSM, 150), _L(CB1, 250)),
        "T8": _ac(50, _L(GB1_BSM, 175), _L(CB1, 250)),
        "T9": _ac(75, _L(GB1_BSM, 175), _L(CB1, 250)),
        "T10": _ac(40, _L(DBM, 60), _L(GB1_BSM, 175), _L(CB1, 250)),
    },
    "F3": {
        "T6": _ac(50, _L(GB1_BSM, 150), _L(CB1, 150)),
        "T7": _ac(50, _L(GB1_BSM, 150), _L(CB1, 225)),
        "T8": _ac(50, _L(GB1_BSM, 150), _L(CB1, 225)),
        "T9": _ac(75, _L(GB1_BSM, 150), _L(CB1, 200)),
        "T10": _ac(40, _L(DBM, 60), _L(GB1_BSM, 150), _L(CB1, 200)),
    },
    "F4": {
        "T6": _ac(50, _L(GB1_BSM, 100), _L(CB1, 150)),
        "T7": _ac(50, _L(GB1_BSM, 150), _L(CB1, 150)),
        "T8": _ac(50, _L(GB1_BSM, 150), _L(CB1, 150)),
        "T9": _ac(75, _L(GB1_BSM, 150), _L(CB1, 150)),
        "T10": _ac(40, _L(DBM, 60), _L(GB1_BSM, 150), _L(CB1, 150)),
    },
}

# ---------------------------------------------------------------------------
# Catalog 7 — AC + DBM + GB1 + CB1 (T9–T10)
# ---------------------------------------------------------------------------
_CATALOG_AC_DBM_CB: dict[str, dict[str, tuple[CatalogLayer, ...]]] = {
    "F1": {
        "T9": _ac(40, _L(DBM, 60), _L(GB1_BSM, 300), _L(CB1, 300)),
        "T10": _ac(50, _L(DBM, 75), _L(GB1_BSM, 300), _L(CB1, 300)),
    },
    "F2": {
        "T9": _ac(40, _L(DBM, 60), _L(GB1_BSM, 300), _L(CB1, 250)),
        "T10": _ac(50, _L(DBM, 75), _L(GB1_BSM, 300), _L(CB1, 250)),
    },
    "F3": {
        "T9": _ac(40, _L(DBM, 60), _L(GB1_BSM, 275), _L(CB1, 200)),
        "T10": _ac(50, _L(DBM, 75), _L(GB1_BSM, 275), _L(CB1, 200)),
    },
    "F4": {
        "T9": _ac(40, _L(DBM, 60), _L(GB1_BSM, 250), _L(CB1, 175)),
        "T10": _ac(50, _L(DBM, 75), _L(GB1_BSM, 250), _L(CB1, 175)),
    },
}

CATALOG_TABLES: dict[str, dict[str, dict[str, tuple[CatalogLayer, ...]]]] = {
    CATALOG_DBST_GRANULAR: _CATALOG_DBST_GRANULAR,
    CATALOG_DBST_GB_CB: _CATALOG_DBST_GB_CB,
    CATALOG_DBST_CB_GS: _CATALOG_DBST_CB_GS,
    CATALOG_AC_GRANULAR: _CATALOG_AC_GRANULAR,
    CATALOG_AC_DBM_GS: _CATALOG_AC_DBM_GS,
    CATALOG_AC_GB_CB: _CATALOG_AC_GB_CB,
    CATALOG_AC_DBM_CB: _CATALOG_AC_DBM_CB,
}


def foundation_from_cbr(cbr_percent: float) -> str:
    """Map subgrade CBR (%) to foundation class label used in the catalogs."""
    cbr = float(cbr_percent)
    if cbr < 7.0:
        return "F1 (S3)"
    if cbr < 14.0:
        return "F2 (S4)"
    if cbr < 30.0:
        return "F3 (S5)"
    return "F4 (S6)"


def normalize_foundation(value: str) -> str | None:
    return FOUNDATION_CODES.get(value.strip())


def available_traffic_classes(catalog_name: str) -> tuple[str, ...]:
    table = CATALOG_TABLES.get(catalog_name, {})
    classes: set[str] = set()
    for traffic_map in table.values():
        classes.update(traffic_map.keys())
    return tuple(sorted(classes, key=lambda code: int(code[1:])))


def lookup_pavement_design(
    *,
    seal_type: str,
    catalog_name: str,
    traffic: str,
    foundation: str,
) -> PavementCatalogDesign | None:
    """Return one catalog design for the selected seal / catalog / T / F combination."""
    table = CATALOG_TABLES.get(catalog_name)
    if table is None:
        return None

    foundation_code = normalize_foundation(foundation)
    if foundation_code is None:
        return None

    layers = table.get(foundation_code, {}).get(traffic)
    if layers is None:
        return None

    # Seal-type consistency check: DBST catalogs must start with DBST; AC with AC/HRA.
    top = layers[0].material if layers else ""
    if seal_type == "DBST" and top != DBST:
        return None
    if seal_type == "AC" and top != AC_HRA:
        return None

    return PavementCatalogDesign(
        seal_type=seal_type,
        catalog_name=catalog_name,
        traffic=traffic,
        foundation=foundation_code,
        layers=layers,
    )


def summarize_pavement_design(design: PavementCatalogDesign | None) -> dict[str, str]:
    if design is None:
        return {}
    return {
        "Seal type": design.seal_type,
        "Traffic": f"{design.traffic} ({TRAFFIC_MSA_RANGES.get(design.traffic, '')})",
        "Foundation": design.foundation,
        "Catalog": design.catalog_name,
        "Total thickness": f"{design.total_thickness_mm:,.0f} mm",
        "Structure": design.layer_summary,
    }
