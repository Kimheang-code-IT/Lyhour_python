"""Tests for flexible pavement catalog lookup tables."""
from app.data.pavement_catalog import (
    AC_HRA,
    CATALOG_AC_DBM_GS,
    CATALOG_DBST_GRANULAR,
    DBST,
    GB1_BSM,
    GB3,
    GS2,
    foundation_from_cbr,
    lookup_pavement_design,
)


def test_foundation_from_cbr() -> None:
    assert foundation_from_cbr(5.0).startswith("F1")
    assert foundation_from_cbr(10.0).startswith("F2")
    assert foundation_from_cbr(20.0).startswith("F3")
    assert foundation_from_cbr(35.0).startswith("F4")


def test_lookup_dbst_granular() -> None:
    design = lookup_pavement_design(
        seal_type="DBST",
        catalog_name=CATALOG_DBST_GRANULAR,
        traffic="T1",
        foundation="F1 (S3)",
    )
    assert design is not None
    assert design.layers[0].material == DBST
    assert design.layers[1].material == GB3
    assert design.layers[1].thickness_mm == 150
    assert design.layers[2].material == GS2
    assert design.layers[2].thickness_mm == 175


def test_lookup_ac_dbm_gs() -> None:
    design = lookup_pavement_design(
        seal_type="AC",
        catalog_name=CATALOG_AC_DBM_GS,
        traffic="T7",
        foundation="F2",
    )
    assert design is not None
    assert design.layers[0].material == AC_HRA
    assert design.layers[0].thickness_mm == 50
    assert design.layers[2].material == GB1_BSM
    assert design.layers[2].thickness_mm == 200


def test_lookup_missing_combination() -> None:
    design = lookup_pavement_design(
        seal_type="AC",
        catalog_name=CATALOG_AC_DBM_GS,
        traffic="T1",
        foundation="F1",
    )
    assert design is None
