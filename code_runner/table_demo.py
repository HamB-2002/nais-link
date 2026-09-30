from decimal import Decimal

from code_runner.models import (
    EvidenceKind,
    EvidenceProvenance,
    Execution,
    ExecutionState,
    IsolationState,
    NumericValue,
    ProofState,
    SourceKind,
    SourceMetadata,
    SourceProof,
    Tolerance,
    Unit,
)
from code_runner.table_models import (
    CellComparison,
    ExecutionTableArtifact,
    ExecutionTableCell,
    QuantitySemantics,
    ReportTableArtifact,
    ReportTableCell,
    TableComparison,
    TableCoordinate,
    TableReconciliationResult,
)
from code_runner.table_workflow import reconcile_tables

type JsonScalar = str | int | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def demo_payload() -> dict[str, JsonValue]:
    result = reconcile_tables((_report_table(),), (_execution_table(),))
    return {
        "mode": "structured_fixture",
        "summary": _summary(result),
        "comparisons": [_comparison_payload(comparison) for comparison in result.comparisons],
    }


def _summary(result: TableReconciliationResult) -> dict[str, int]:
    cells = tuple(
        cell for comparison in result.comparisons for cell in comparison.cell_results
    )
    return {
        "report_tables": len(result.comparisons),
        "matched_tables": sum(comparison.execution_table_id is not None for comparison in result.comparisons),
        "cells": len(cells),
        "match": sum(cell.status.value == "match" for cell in cells),
        "mismatch": sum(cell.status.value == "mismatch" for cell in cells),
        "review": sum(cell.status.value == "needs_human_review" for cell in cells),
    }


def _comparison_payload(comparison: TableComparison) -> dict[str, JsonValue]:
    return {
        "report_table_id": comparison.report_table_id,
        "execution_table_id": comparison.execution_table_id or "미연결",
        "status": comparison.status.value,
        "pairing_reasons": list(comparison.pairing_reasons),
        "cells": [_cell_payload(cell) for cell in comparison.cell_results],
        "unmatched_execution_cells": [
            _coordinate_payload(coordinate)
            for coordinate in comparison.unmatched_execution_cells
        ],
    }


def _cell_payload(cell: CellComparison) -> dict[str, JsonValue]:
    return {
        "coordinate": _coordinate_payload(cell.report_coordinate),
        "execution_coordinate": (
            None
            if cell.execution_coordinate is None
            else _coordinate_payload(cell.execution_coordinate)
        ),
        "reported": _numeric_payload(cell.reported_value),
        "execution": (
            None if cell.execution_value is None else _numeric_payload(cell.execution_value)
        ),
        "status": cell.status.value,
        "reason_codes": list(cell.reason_codes),
        "output_locator": cell.output_locator,
    }


def _coordinate_payload(coordinate: TableCoordinate) -> dict[str, JsonValue]:
    return {
        "panel": coordinate.panel,
        "row": coordinate.row_key,
        "columns": list(coordinate.column_path),
    }


def _numeric_payload(value: NumericValue) -> dict[str, JsonValue]:
    return {"value": str(value.amount), "unit": value.unit.value}


def _report_table() -> ReportTableArtifact:
    return ReportTableArtifact(
        "report-table-3",
        "서울 만족도 요약",
        (
            _report_cell("서울", "15.0%"),
            _report_cell("부산", "13.7%"),
        ),
    )


def _execution_table() -> ExecutionTableArtifact:
    return ExecutionTableArtifact(
        "run-table-summary",
        "만족도 서울 요약",
        (
            _execution_cell("부산", Decimal("13.74")),
            _execution_cell("서울", Decimal("15.02")),
        ),
        "run-demo-001",
    )


def _report_cell(row: str, raw_value: str) -> ReportTableCell:
    return ReportTableCell(
        _coordinate(row),
        NumericValue(Decimal(raw_value.removesuffix("%")), Unit.PERCENT),
        raw_value,
        _semantics(),
        SourceMetadata(
            SourceKind.RESEARCH_RESULT,
            True,
            table_id="표 3",
            row=row,
            column="평균 만족도",
            cell_text=raw_value,
        ),
        Tolerance(Decimal("0.1"), None, 1),
    )


def _execution_cell(row: str, amount: Decimal) -> ExecutionTableCell:
    proof = SourceProof(ProofState.VERIFIED, "sha256:demo-run")
    value = NumericValue(amount, Unit.PERCENT)
    return ExecutionTableCell(
        _coordinate(row),
        value,
        _semantics(),
        Execution(
            True,
            IsolationState.AVAILABLE,
            ExecutionState.COMPLETED,
            value,
            provenance=EvidenceProvenance(EvidenceKind.SOURCE_REPRODUCTION, proof, proof, proof),
        ),
        f"outputs/summary.json#/rows/{row}/mean_satisfaction",
    )


def _coordinate(row: str) -> TableCoordinate:
    return TableCoordinate("응답자", row, ("평균 만족도",))


def _semantics() -> QuantitySemantics:
    return QuantitySemantics(
        "만족도",
        "2025",
        "서울·부산 응답자",
        "유효 응답자",
        "mean(score)",
    )
