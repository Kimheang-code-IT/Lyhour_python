"""Tests for DCP analysis calculations."""
from app.data.dcp_analysis import DcpInputRow, analyze_dcp_rows, cbr_from_penetration_index, summarize_dcp_analysis


def test_analyze_dcp_rows_sample() -> None:
    rows = [
        DcpInputRow(0, 0),
        DcpInputRow(4, 60),
        DcpInputRow(4, 130),
        DcpInputRow(5, 150),
    ]
    result = analyze_dcp_rows(rows)

    assert len(result) == 4
    assert result[1].total_blow_number == 4
    assert result[2].total_blow_number == 8
    assert result[2].change_penetration_mm == 70
    assert result[2].penetration_index_mm_per_blow == 17.5
    assert round(result[2].cbr_percent or 0, 2) == round(cbr_from_penetration_index(17.5) or 0, 2)


def test_analyze_dcp_rows_first_row_has_no_cbr() -> None:
    result = analyze_dcp_rows([DcpInputRow(0, 0)])
    assert result[0].change_penetration_mm is None
    assert result[0].cbr_percent is None


def test_summarize_dcp_analysis() -> None:
    rows = analyze_dcp_rows(
        [
            DcpInputRow(0, 0),
            DcpInputRow(4, 60),
            DcpInputRow(4, 130),
        ]
    )
    summary = summarize_dcp_analysis(rows)
    assert summary["Number of layers"] == "3"
    assert summary["Maximum depth"] == "130 mm"
    assert summary["Total blow number"] == "8"
    assert "CBR at max depth" in summary
