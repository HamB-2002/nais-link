from dataclasses import replace
from decimal import Decimal

from code_runner.comparison import evaluate
from code_runner.models import (
    Claim,
    ComparisonRequest,
    Execution,
    ExecutionState,
    IsolationState,
    NumericValue,
    ReviewStatus,
    SemanticMatch,
    Tolerance,
    Trace,
    TraceConfidence,
    Unit,
)


def test_evaluate_returns_match_when_ratio_rounds_to_reported_percent() -> None:
    # Given: 동일 의미 조건과 87.5%로 환산되는 비율 실행값
    request = _request(evidence=NumericValue(Decimal("0.875"), Unit.RATIO))
    request = replace(
        request,
        claim=replace(request.claim, value=NumericValue(Decimal("87.5"), Unit.PERCENT)),
    )

    # When: 보고서 수치와 실행값을 대조하면
    result = evaluate(request)

    # Then: 단위 변환 후 일치로 판정한다.
    assert result.status is ReviewStatus.MATCH
    assert result.normalized_evidence == NumericValue(Decimal("87.5"), Unit.PERCENT)


def test_evaluate_returns_mismatch_when_value_exceeds_tolerance() -> None:
    # Given: 보고서 2.7배보다 허용오차 밖인 재실행 값
    request = _request(evidence=NumericValue(Decimal("2.41"), Unit.MULTIPLE))

    # When: 수치를 대조하면
    result = evaluate(request)

    # Then: 실행 실패가 아닌 불일치로 판정한다.
    assert result.status is ReviewStatus.MISMATCH
    assert result.reason_codes == ("VALUE_OUTSIDE_TOLERANCE",)


def test_evaluate_returns_not_comparable_when_trace_semantics_differ() -> None:
    # Given: 기간 조건이 다른 연결 근거
    trace = Trace(
        confidence=TraceConfidence.HIGH,
        metric=SemanticMatch.EXACT,
        period=SemanticMatch.MISMATCH,
        population=SemanticMatch.EXACT,
        denominator=SemanticMatch.EXACT,
        formula=SemanticMatch.EXACT,
    )
    request = _request(evidence=NumericValue(Decimal("2.7"), Unit.MULTIPLE), trace=trace)

    # When: 수치를 대조하면
    result = evaluate(request)

    # Then: 숫자가 같아도 비교 불가다.
    assert result.status is ReviewStatus.NOT_COMPARABLE


def test_evaluate_returns_evidence_incomplete_when_contract_is_missing() -> None:
    # Given: 실행 계약이 완성되지 않은 요청
    execution = Execution(
        contract_complete=False,
        isolation=IsolationState.AVAILABLE,
        state=ExecutionState.NOT_STARTED,
        evidence=None,
    )
    request = _request(evidence=None, execution=execution)

    # When: 대조를 요청하면
    result = evaluate(request)

    # Then: 실행하지 않고 근거 부족을 반환한다.
    assert result.status is ReviewStatus.EVIDENCE_INCOMPLETE


def test_evaluate_returns_isolation_unavailable_without_executing_code() -> None:
    # Given: Docker 격리 환경을 확인할 수 없는 요청
    execution = Execution(
        contract_complete=True,
        isolation=IsolationState.UNAVAILABLE,
        state=ExecutionState.NOT_STARTED,
        evidence=None,
    )
    request = _request(evidence=None, execution=execution)

    # When: 대조를 요청하면
    result = evaluate(request)

    # Then: 로컬 실행 대신 격리 불가를 반환한다.
    assert result.status is ReviewStatus.ISOLATION_UNAVAILABLE


def test_evaluate_returns_execution_failed_when_isolated_run_fails() -> None:
    # Given: Docker는 가능하지만 실행이 실패한 요청
    execution = Execution(
        contract_complete=True,
        isolation=IsolationState.AVAILABLE,
        state=ExecutionState.FAILED,
        evidence=None,
    )
    request = _request(evidence=None, execution=execution)

    # When: 대조를 요청하면
    result = evaluate(request)

    # Then: 값 불일치가 아닌 실행 실패를 반환한다.
    assert result.status is ReviewStatus.EXECUTION_FAILED


def test_evaluate_returns_needs_human_review_when_trace_confidence_is_low() -> None:
    # Given: 자동 연결 신뢰도가 낮은 Trace
    trace = Trace(
        confidence=TraceConfidence.LOW,
        metric=SemanticMatch.EXACT,
        period=SemanticMatch.EXACT,
        population=SemanticMatch.EXACT,
        denominator=SemanticMatch.EXACT,
        formula=SemanticMatch.EXACT,
    )
    request = _request(evidence=NumericValue(Decimal("2.7"), Unit.MULTIPLE), trace=trace)

    # When: 대조를 요청하면
    result = evaluate(request)

    # Then: 사람이 연결 근거를 확인해야 한다.
    assert result.status is ReviewStatus.NEEDS_HUMAN_REVIEW


def _request(
    evidence: NumericValue | None,
    trace: Trace | None = None,
    execution: Execution | None = None,
) -> ComparisonRequest:
    claim = Claim(
        claim_id="C-042",
        value=NumericValue(Decimal("2.7"), Unit.MULTIPLE),
        metric="처리 속도 개선 배수",
        period="2025년 실험",
        population="시험 데이터셋 A",
        denominator="기존 방법 평균 처리 시간",
    )
    exact_trace = Trace(
        confidence=TraceConfidence.HIGH,
        metric=SemanticMatch.EXACT,
        period=SemanticMatch.EXACT,
        population=SemanticMatch.EXACT,
        denominator=SemanticMatch.EXACT,
        formula=SemanticMatch.EXACT,
    )
    completed_execution = Execution(
        contract_complete=True,
        isolation=IsolationState.AVAILABLE,
        state=ExecutionState.COMPLETED,
        evidence=evidence,
    )
    return ComparisonRequest(
        claim=claim,
        trace=exact_trace if trace is None else trace,
        execution=completed_execution if execution is None else execution,
        tolerance=Tolerance(
            absolute=Decimal("0.05"),
            relative=None,
            rounding_digits=1,
        ),
    )
