from collections import defaultdict
from dataclasses import replace

from code_runner.models import (
    Claim,
    ComparisonRequest,
    ReviewStatus,
    SemanticMatch,
    Trace,
    TraceConfidence,
)
from code_runner.table_models import (
    CellComparison,
    ExecutionTableArtifact,
    ExecutionTableCell,
    QuantitySemantics,
    ReportTableArtifact,
    ReportTableCell,
    TableCandidate,
    TableComparison,
    TableCoordinate,
    TablePairStatus,
)
from code_runner.tolerance_policy import policy_for
from code_runner.workflow import evaluate


def compare_table_pair(
    report: ReportTableArtifact,
    execution: ExecutionTableArtifact,
    candidate: TableCandidate,
) -> TableComparison:
    execution_by_key = execution_cells_by_key(execution.cells)
    cell_results = tuple(
        compare_cell(report_cell, execution_by_key.get(coordinate_key(report_cell.coordinate), ()))
        for report_cell in report.cells
    )
    report_keys = coordinate_keys(report.cells)
    unmatched_execution_cells = tuple(
        cell.coordinate for cell in execution.cells if coordinate_key(cell.coordinate) not in report_keys
    )
    return TableComparison(
        TablePairStatus.MATCHED,
        report.table_id,
        execution.table_id,
        candidate.reasons,
        cell_results,
        unmatched_execution_cells,
    )


def compare_cell(
    report: ReportTableCell, execution_candidates: tuple[ExecutionTableCell, ...]
) -> CellComparison:
    match execution_candidates:
        case ():
            return CellComparison(
                report.coordinate,
                None,
                report.value,
                None,
                ReviewStatus.NEEDS_HUMAN_REVIEW,
                ("EXECUTION_CELL_MISSING",),
                None,
                None,
                None,
            )
        case (execution,):
            policy = policy_for(report.semantics, report.value, report.tolerance_policy)
            if policy is None:
                return CellComparison(
                    report.coordinate,
                    execution.coordinate,
                    report.value,
                    execution.value,
                    ReviewStatus.NEEDS_HUMAN_REVIEW,
                    ("TOLERANCE_POLICY_MISSING",),
                    None,
                    execution.output_locator,
                    None,
                )
            trace = trace_for(report.semantics, execution.semantics)
            request = ComparisonRequest(
                claim_for(report), trace, replace(execution.execution, evidence=execution.value), policy.tolerance
            )
            review = evaluate(request)
            return CellComparison(
                report.coordinate,
                execution.coordinate,
                report.value,
                execution.value,
                review.status,
                review.reason_codes,
                review,
                execution.output_locator,
                policy,
            )
        case _:
            return CellComparison(
                report.coordinate,
                None,
                report.value,
                None,
                ReviewStatus.NEEDS_HUMAN_REVIEW,
                ("DUPLICATE_EXECUTION_CELL_KEY",),
                None,
                None,
                None,
            )


def coordinate_keys(
    cells: tuple[ReportTableCell, ...] | tuple[ExecutionTableCell, ...],
) -> set[tuple[str, str, tuple[str, ...]]]:
    return {coordinate_key(cell.coordinate) for cell in cells}


def coordinate_key(coordinate: TableCoordinate) -> tuple[str, str, tuple[str, ...]]:
    return (
        normalized(coordinate.panel or ""),
        normalized(coordinate.row_key),
        tuple(normalized(part) for part in coordinate.column_path),
    )


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def claim_for(cell: ReportTableCell) -> Claim:
    semantics = cell.semantics
    return Claim(
        claim_id(cell.coordinate),
        cell.value,
        semantics.metric or "unknown",
        semantics.period or "unknown",
        semantics.population or "unknown",
        semantics.denominator or "unknown",
        raw_value=cell.raw_value,
        source=cell.source,
    )


def trace_for(report: QuantitySemantics, execution: QuantitySemantics) -> Trace:
    return Trace(
        TraceConfidence.HIGH,
        semantic_match(report.metric, execution.metric),
        semantic_match(report.period, execution.period),
        semantic_match(report.population, execution.population),
        semantic_match(report.denominator, execution.denominator),
        semantic_match(report.formula, execution.formula),
    )


def semantic_match(report: str | None, execution: str | None) -> SemanticMatch:
    if report is None or execution is None:
        return SemanticMatch.UNKNOWN
    if normalized(report) == normalized(execution):
        return SemanticMatch.EXACT
    return SemanticMatch.MISMATCH


def execution_cells_by_key(
    cells: tuple[ExecutionTableCell, ...],
) -> dict[tuple[str, str, tuple[str, ...]], tuple[ExecutionTableCell, ...]]:
    grouped: defaultdict[tuple[str, str, tuple[str, ...]], list[ExecutionTableCell]] = defaultdict(list)
    for cell in cells:
        grouped[coordinate_key(cell.coordinate)].append(cell)
    return {key: tuple(value) for key, value in grouped.items()}


def claim_id(coordinate: TableCoordinate) -> str:
    return "table:" + ":".join((*coordinate.column_path, coordinate.row_key))
