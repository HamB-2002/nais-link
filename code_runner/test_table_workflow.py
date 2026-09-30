from dataclasses import replace
from decimal import Decimal

from code_runner.models import (
    EvidenceKind,
    EvidenceProvenance,
    Execution,
    ExecutionState,
    IsolationState,
    MetricFamily,
    NumericValue,
    ProofState,
    ReviewStatus,
    SourceKind,
    SourceMetadata,
    SourceProof,
    Tolerance,
    TolerancePolicy,
    TolerancePolicySource,
    Unit,
)
from code_runner.table_models import (
    ExecutionTableArtifact,
    ExecutionTableCell,
    QuantitySemantics,
    ReportTableArtifact,
    ReportTableCell,
    TableCoordinate,
    TablePairStatus,
)
from code_runner.table_workflow import reconcile_tables


def test_reconcile_tables_automatically_pairs_reordered_structured_tables() -> None:
    # Given: 제목과 셀 좌표가 같은 보고서·실행 표 컬렉션
    report = _report_table("report-3", "서울 만족도 요약", (_report_cell(),))
    execution = _execution_table("output-a", "만족도 서울 요약", (_execution_cell(),))

    # When: 표 컬렉션을 대조하면
    result = reconcile_tables((report,), (execution,))

    # Then: 사용자가 표를 지정하지 않아도 자동 연결하고 셀을 일치로 판정한다.
    comparison = result.comparisons[0]
    assert comparison.status is TablePairStatus.MATCHED
    assert comparison.execution_table_id == "output-a"
    assert comparison.cell_results[0].status is ReviewStatus.MATCH


def test_reconcile_tables_blocks_equal_values_with_different_aggregation() -> None:
    # Given: 표면값은 같지만 평균과 합계의 산식이 다른 동일 좌표 셀
    report = _report_table("report-3", "서울 만족도 요약", (_report_cell(),))
    execution = _execution_table(
        "output-a", "서울 만족도 요약", (_execution_cell(formula="sum(score)"),)
    )

    # When: 표 컬렉션을 대조하면
    result = reconcile_tables((report,), (execution,))

    # Then: 값 일치가 아닌 비교 불가를 반환한다.
    assert result.comparisons[0].cell_results[0].status is ReviewStatus.NOT_COMPARABLE


def test_reconcile_tables_keeps_missing_and_extra_cells_visible() -> None:
    # Given: 실행 표에 보고서 셀이 하나 빠지고 코드 전용 셀이 하나 더 있다.
    report = _report_table(
        "report-3",
        "서울 만족도 요약",
        (_report_cell(), _report_cell(row_key="부산")),
    )
    execution = _execution_table(
        "output-a",
        "서울 만족도 요약",
        (_execution_cell(), _execution_cell(row_key="대구")),
    )

    # When: 표 컬렉션을 대조하면
    result = reconcile_tables((report,), (execution,))

    # Then: 누락과 추가 구조를 성공으로 감추지 않는다.
    comparison = result.comparisons[0]
    assert comparison.cell_results[1].reason_codes == ("EXECUTION_CELL_MISSING",)
    assert comparison.unmatched_execution_cells[0].row_key == "대구"


def test_reconcile_tables_keeps_tied_table_candidates_for_review() -> None:
    # Given: 동일한 근거 점수의 실행 표 후보가 둘 있다.
    report = _report_table("report-3", "서울 만족도 요약", (_report_cell(),))
    first = _execution_table("output-a", "서울 만족도 요약", (_execution_cell(),))
    second = _execution_table("output-b", "서울 만족도 요약", (_execution_cell(),))

    # When: 표 컬렉션을 대조하면
    result = reconcile_tables((report,), (first, second))

    # Then: 임의의 첫 표를 고르지 않고 검토 대상으로 남긴다.
    comparison = result.comparisons[0]
    assert comparison.status is TablePairStatus.AMBIGUOUS
    assert comparison.cell_results[0].status is ReviewStatus.NEEDS_HUMAN_REVIEW


def test_reconcile_tables_holds_generic_metric_without_tolerance_policy() -> None:
    # Given: 지표별 허용오차 근거가 없는 일반 지수 표 셀
    report_cell = replace(
        _report_cell(),
        semantics=replace(_report_cell().semantics, metric="삶의 질 종합 지수"),
        value=NumericValue(Decimal("15.0"), Unit.MULTIPLE),
    )
    execution_cell = replace(
        _execution_cell(),
        semantics=replace(_execution_cell().semantics, metric="삶의 질 종합 지수"),
        value=NumericValue(Decimal("15.02"), Unit.MULTIPLE),
        execution=replace(
            _execution_cell().execution,
            evidence=NumericValue(Decimal("15.02"), Unit.MULTIPLE),
        ),
    )
    report = _report_table("report-3", "삶의 질 요약", (report_cell,))
    execution = _execution_table("output-a", "삶의 질 요약", (execution_cell,))

    # When: 자동 표 대조를 수행하면
    result = reconcile_tables((report,), (execution,))

    # Then: 임의의 공통 허용오차로 일치시키지 않고 검토로 보낸다.
    cell = result.comparisons[0].cell_results[0]
    assert cell.status is ReviewStatus.NEEDS_HUMAN_REVIEW
    assert cell.reason_codes == ("TOLERANCE_POLICY_MISSING",)


def test_reconcile_tables_prioritizes_report_declared_tolerance_policy() -> None:
    # Given: 비율 카탈로그보다 더 엄격한 보고서 선언 허용오차
    report_cell = replace(
        _report_cell(),
        tolerance_policy=TolerancePolicy(
            "report.table-3.precision",
            MetricFamily.RATE,
            Tolerance(Decimal("0.01"), None, 2),
            TolerancePolicySource.REPORT_DECLARED,
            "표 3 각주의 재현 허용오차",
            "표 3 각주",
        ),
    )
    report = _report_table("report-3", "서울 만족도 요약", (report_cell,))
    execution = _execution_table("output-a", "서울 만족도 요약", (_execution_cell(),))

    # When: 보고서 자릿수까지 보존한 0.02%p 차이의 실행값을 대조하면
    result = reconcile_tables((report,), (execution,))

    # Then: 0.1%p·한 자리 카탈로그가 아닌 보고서 선언 정책으로 불일치가 된다.
    cell = result.comparisons[0].cell_results[0]
    assert cell.status is ReviewStatus.MISMATCH
    assert cell.tolerance_policy is not None
    assert cell.tolerance_policy.policy_id == "report.table-3.precision"


def _report_table(
    table_id: str, title: str, cells: tuple[ReportTableCell, ...]
) -> ReportTableArtifact:
    return ReportTableArtifact(table_id, title, cells)


def _execution_table(
    table_id: str, title: str, cells: tuple[ExecutionTableCell, ...]
) -> ExecutionTableArtifact:
    return ExecutionTableArtifact(table_id, title, cells, "run-demo-001")


def _report_cell(row_key: str = "서울") -> ReportTableCell:
    return ReportTableCell(
        _coordinate(row_key),
        NumericValue(Decimal("15.0"), Unit.PERCENT),
        "15.0%",
        _semantics(),
        SourceMetadata(
            SourceKind.RESEARCH_RESULT,
            True,
            table_id="표 3",
            row=row_key,
            column="평균 만족도",
            cell_text="15.0%",
        ),
        Tolerance(Decimal("0.1"), None, 1),
    )


def _execution_cell(
    row_key: str = "서울", formula: str = "mean(score)"
) -> ExecutionTableCell:
    proof = SourceProof(ProofState.VERIFIED, "sha256:demo")
    return ExecutionTableCell(
        _coordinate(row_key),
        NumericValue(Decimal("15.02"), Unit.PERCENT),
        _semantics(formula=formula),
        Execution(
            True,
            IsolationState.AVAILABLE,
            ExecutionState.COMPLETED,
            NumericValue(Decimal("15.02"), Unit.PERCENT),
            provenance=EvidenceProvenance(EvidenceKind.SOURCE_REPRODUCTION, proof, proof, proof),
        ),
        f"outputs/summary.json#/rows/{row_key}",
    )


def _coordinate(row_key: str) -> TableCoordinate:
    return TableCoordinate("응답자", row_key, ("평균 만족도",))


def _semantics(formula: str = "mean(score)") -> QuantitySemantics:
    return QuantitySemantics("만족도", "2025", "서울 응답자", "유효 응답자", formula)
