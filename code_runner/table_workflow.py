from typing import assert_never

from code_runner.models import ReviewStatus
from code_runner.table_alignment import compare_table_pair, coordinate_keys, normalized
from code_runner.table_models import (
    CellComparison,
    ExecutionTableArtifact,
    ReportTableArtifact,
    TableCandidate,
    TableComparison,
    TablePairStatus,
    TableReconciliationResult,
)


def reconcile_tables(
    report_tables: tuple[ReportTableArtifact, ...],
    execution_tables: tuple[ExecutionTableArtifact, ...],
) -> TableReconciliationResult:
    candidates = _candidates(report_tables, execution_tables)
    matched_execution_ids: set[str] = set()
    comparisons = tuple(
        _compare_report_table(report, execution_tables, candidates, matched_execution_ids)
        for report in report_tables
    )
    unmatched_execution_tables = tuple(
        table.table_id
        for table in execution_tables
        if table.table_id not in matched_execution_ids
    )
    return TableReconciliationResult(comparisons, unmatched_execution_tables)


def _compare_report_table(
    report: ReportTableArtifact,
    execution_tables: tuple[ExecutionTableArtifact, ...],
    candidates: tuple[TableCandidate, ...],
    matched_execution_ids: set[str],
) -> TableComparison:
    available = tuple(
        candidate
        for candidate in candidates
        if candidate.report_table_id == report.table_id
        and candidate.execution_table_id not in matched_execution_ids
    )
    best = _best_candidate(available)
    match best:
        case None:
            return _unmatched_table(report)
        case TableCandidate() if _is_ambiguous(best, available):
            return _ambiguous_table(report, best, available)
        case TableCandidate():
            execution = _execution_table(execution_tables, best.execution_table_id)
            matched_execution_ids.add(execution.table_id)
            return compare_table_pair(report, execution, best)
        case unreachable:
            assert_never(unreachable)


def _candidates(
    report_tables: tuple[ReportTableArtifact, ...],
    execution_tables: tuple[ExecutionTableArtifact, ...],
) -> tuple[TableCandidate, ...]:
    return tuple(
        candidate
        for report in report_tables
        for execution in execution_tables
        if (candidate := _candidate(report, execution)) is not None
    )


def _candidate(
    report: ReportTableArtifact, execution: ExecutionTableArtifact
) -> TableCandidate | None:
    title_tokens = _tokens(report.title) & _tokens(execution.title)
    shared_coordinates = coordinate_keys(report.cells) & coordinate_keys(execution.cells)
    score = len(title_tokens) * 3 + len(shared_coordinates) * 2
    if score == 0:
        return None
    reasons: list[str] = []
    if title_tokens:
        reasons.append(f"TITLE_TOKEN_OVERLAP:{','.join(sorted(title_tokens))}")
    if shared_coordinates:
        reasons.append(f"SHARED_CELL_KEYS:{len(shared_coordinates)}")
    return TableCandidate(report.table_id, execution.table_id, score, tuple(reasons))


def _best_candidate(candidates: tuple[TableCandidate, ...]) -> TableCandidate | None:
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate.score)


def _is_ambiguous(best: TableCandidate, candidates: tuple[TableCandidate, ...]) -> bool:
    return sum(candidate.score == best.score for candidate in candidates) > 1


def _unmatched_table(report: ReportTableArtifact) -> TableComparison:
    cell_results = tuple(
        CellComparison(
            cell.coordinate,
            None,
            cell.value,
            None,
            ReviewStatus.NEEDS_HUMAN_REVIEW,
            ("NO_EXECUTION_TABLE_CANDIDATE",),
            None,
            None,
        )
        for cell in report.cells
    )
    return TableComparison(
        TablePairStatus.UNMATCHED,
        report.table_id,
        None,
        ("NO_EXECUTION_TABLE_CANDIDATE",),
        cell_results,
        (),
    )


def _ambiguous_table(
    report: ReportTableArtifact,
    best: TableCandidate,
    candidates: tuple[TableCandidate, ...],
) -> TableComparison:
    execution_ids = ",".join(
        sorted(candidate.execution_table_id for candidate in candidates if candidate.score == best.score)
    )
    reason = f"AMBIGUOUS_TABLE_CANDIDATES:{execution_ids}"
    cell_results = tuple(
        CellComparison(
            cell.coordinate,
            None,
            cell.value,
            None,
            ReviewStatus.NEEDS_HUMAN_REVIEW,
            (reason,),
            None,
            None,
        )
        for cell in report.cells
    )
    return TableComparison(TablePairStatus.AMBIGUOUS, report.table_id, None, (reason,), cell_results, ())


def _execution_table(
    tables: tuple[ExecutionTableArtifact, ...], table_id: str
) -> ExecutionTableArtifact:
    return next(table for table in tables if table.table_id == table_id)


def _tokens(value: str) -> set[str]:
    return {token for token in normalized(value).split() if token}
