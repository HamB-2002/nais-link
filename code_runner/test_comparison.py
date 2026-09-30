from dataclasses import replace
from decimal import Decimal

import pytest

from code_runner.models import (
    Claim,
    ComparisonMode,
    ComparisonRequest,
    EvidenceKind,
    EvidenceProvenance,
    Execution,
    ExecutionState,
    IsolationState,
    NumericValue,
    ProofState,
    ReviewStatus,
    SemanticMatch,
    SourceProof,
    Threshold,
    ThresholdOperator,
    Tolerance,
    Trace,
    TraceConfidence,
    Unit,
)
from code_runner.tolerance_policy import catalog_policy
from code_runner.workflow import evaluate


def test_evaluate_returns_match_when_ratio_rounds_to_reported_percent() -> None:
    # Given: 87.5% 보고서 값과 동일한 비율 실행값
    request = _request(NumericValue(Decimal("0.875"), Unit.RATIO))
    request = replace(
        request,
        claim=replace(request.claim, value=NumericValue(Decimal("87.5"), Unit.PERCENT)),
    )

    # When: 검증된 원본 재현값을 대조하면
    result = evaluate(request)

    # Then: 보고서 단위로 환산·반올림해 일치한다.
    assert result.status is ReviewStatus.MATCH
    assert result.rounded_evidence_in_report_unit == NumericValue(
        Decimal("87.5"), Unit.PERCENT
    )


@pytest.mark.parametrize(
    ("claim_value", "evidence", "digits"),
    [
        (
            NumericValue(Decimal(1200), Unit.MILLISECOND),
            NumericValue(Decimal("1.2"), Unit.SECOND),
            0,
        ),
        (
            NumericValue(Decimal(1500000), Unit.WON),
            NumericValue(Decimal("1.5"), Unit.MILLION_WON),
            0,
        ),
        (
            NumericValue(Decimal("3.5"), Unit.HUNDRED_MILLION_WON),
            NumericValue(Decimal("3.54"), Unit.HUNDRED_MILLION_WON),
            1,
        ),
    ],
)
def test_evaluate_rounds_evidence_in_report_unit(
    claim_value: NumericValue, evidence: NumericValue, digits: int
) -> None:
    # Given: 단위 스케일이 다른 등가값 또는 보고서 자릿수 차이
    claim = replace(_request(evidence).claim, value=claim_value)
    request = _request(
        evidence, claim=claim, tolerance=Tolerance(Decimal(0), None, digits)
    )

    # When: 보고서 단위로 바꾼 뒤 반올림해 대조하면
    result = evaluate(request)

    # Then: 정규화 단위 자릿수와 무관하게 일치한다.
    assert result.status is ReviewStatus.MATCH
    assert result.rounded_evidence_in_report_unit == claim_value


def test_evaluate_returns_mismatch_when_value_exceeds_tolerance() -> None:
    # Given: 보고서 2.7배보다 허용오차 밖인 원본 재현값
    request = _request(NumericValue(Decimal("2.41"), Unit.MULTIPLE))

    # When: 대조하면
    result = evaluate(request)

    # Then: 실행 실패가 아닌 불일치다.
    assert result.status is ReviewStatus.MISMATCH


@pytest.mark.parametrize(
    ("metric", "claim_value", "evidence", "expected_status"),
    [
        (
            "평균 신장",
            NumericValue(Decimal("170.0"), Unit.CENTIMETER),
            NumericValue(Decimal("170.4"), Unit.CENTIMETER),
            ReviewStatus.MATCH,
        ),
        (
            "평균 체중",
            NumericValue(Decimal("70.0"), Unit.KILOGRAM),
            NumericValue(Decimal("70.4"), Unit.KILOGRAM),
            ReviewStatus.MISMATCH,
        ),
    ],
)
def test_evaluate_uses_metric_specific_tolerance_policy(
    metric: str,
    claim_value: NumericValue,
    evidence: NumericValue,
    expected_status: ReviewStatus,
) -> None:
    # Given: 동일한 0.4 차이지만 신장과 체중의 승인 정책이 다른 Claim
    policy = catalog_policy(metric, claim_value.unit)
    assert policy is not None
    claim = replace(_request(evidence).claim, metric=metric, value=claim_value)
    request = _request(evidence, claim=claim, tolerance=policy.tolerance)

    # When: 승인된 정책의 허용오차로 대조하면
    result = evaluate(request)

    # Then: 신장은 일치, 체중은 불일치로 구분한다.
    assert result.status is expected_status


def test_evaluate_prioritizes_semantic_mismatch_over_execution_failure() -> None:
    # Given: 기간 불일치와 실행 실패가 함께 존재하는 요청
    execution = Execution(
        True,
        IsolationState.AVAILABLE,
        ExecutionState.FAILED,
        None,
        provenance=_source_provenance(),
    )

    # When: 상태를 대조하면
    result = evaluate(
        _request(None, trace=_trace(period=SemanticMatch.MISMATCH), execution=execution)
    )

    # Then: 실행 실패가 아닌 비교 불가를 먼저 반환한다.
    assert result.status is ReviewStatus.NOT_COMPARABLE


def test_evaluate_prioritizes_semantic_mismatch_over_low_confidence() -> None:
    # Given: 명백한 분모 불일치와 낮은 Trace 신뢰도
    trace = _trace(confidence=TraceConfidence.LOW, denominator=SemanticMatch.MISMATCH)

    # When: 상태를 대조하면
    result = evaluate(
        _request(NumericValue(Decimal("2.7"), Unit.MULTIPLE), trace=trace)
    )

    # Then: 사람이 검토하기 전 비교 불가를 반환한다.
    assert result.status is ReviewStatus.NOT_COMPARABLE


def test_evaluate_returns_evidence_incomplete_without_provenance() -> None:
    # Given: 원본 재현 근거가 빠진 기존 형태의 완료 요청
    execution = Execution(
        True,
        IsolationState.AVAILABLE,
        ExecutionState.COMPLETED,
        NumericValue(Decimal("2.7"), Unit.MULTIPLE),
    )

    # When: 대조하면
    result = evaluate(_request(None, execution=execution))

    # Then: 자동 일치 판정을 만들지 않는다.
    assert result.reason_codes == ("EVIDENCE_PROVENANCE_MISSING",)


def test_evaluate_returns_human_review_for_independent_recalculation() -> None:
    # Given: 표를 바탕으로 한 독립 재계산 결과
    execution = Execution(
        True,
        IsolationState.AVAILABLE,
        ExecutionState.COMPLETED,
        NumericValue(Decimal("2.7"), Unit.MULTIPLE),
        provenance=_independent_provenance(),
    )

    # When: 계산값이 같아도 대조하면
    result = evaluate(_request(None, execution=execution))

    # Then: 원본 재현이 아닌 사람 검토 결과와 disclosure를 남긴다.
    assert result.status is ReviewStatus.NEEDS_HUMAN_REVIEW
    assert result.disclosure is not None


def test_evaluate_supports_threshold_probability_condition() -> None:
    # Given: p < 0.001 임계값 Claim과 검증된 원본 재현값
    claim = Claim(
        "P-001",
        NumericValue(Decimal("0.001"), Unit.PERCENT),
        "p-value",
        "2025",
        "A",
        "test",
        comparison_mode=ComparisonMode.THRESHOLD,
        threshold=Threshold(
            ThresholdOperator.LESS_THAN, NumericValue(Decimal("0.001"), Unit.PERCENT)
        ),
    )
    request = _request(NumericValue(Decimal("0.0009"), Unit.PERCENT), claim=claim)

    # When: 부등식 정책으로 대조하면
    result = evaluate(request)

    # Then: 숫자 동등 비교가 아닌 임계값 만족으로 판정한다.
    assert result.reason_codes == ("THRESHOLD_SATISFIED",)


def test_evaluate_keeps_isolation_unavailable_before_provenance() -> None:
    # Given: Docker를 확인할 수 없는 요청
    execution = Execution(
        True, IsolationState.UNAVAILABLE, ExecutionState.NOT_STARTED, None
    )

    # When: 대조하면
    result = evaluate(_request(None, execution=execution))

    # Then: 로컬 실행 대신 격리 불가를 반환한다.
    assert result.status is ReviewStatus.ISOLATION_UNAVAILABLE


def _request(
    evidence: NumericValue | None,
    trace: Trace | None = None,
    execution: Execution | None = None,
    claim: Claim | None = None,
    tolerance: Tolerance | None = None,
) -> ComparisonRequest:
    base_claim = Claim(
        "C-042",
        NumericValue(Decimal("2.7"), Unit.MULTIPLE),
        "처리 속도 개선 배수",
        "2025년 실험",
        "시험 데이터셋 A",
        "기존 방법 평균 처리 시간",
    )
    base_execution = Execution(
        True,
        IsolationState.AVAILABLE,
        ExecutionState.COMPLETED,
        evidence,
        provenance=_source_provenance(),
    )
    return ComparisonRequest(
        claim or base_claim,
        trace or _trace(),
        execution or base_execution,
        tolerance or Tolerance(Decimal("0.05"), None, 1),
    )


def _trace(
    confidence: TraceConfidence = TraceConfidence.HIGH,
    period: SemanticMatch = SemanticMatch.EXACT,
    denominator: SemanticMatch = SemanticMatch.EXACT,
) -> Trace:
    return Trace(
        confidence,
        SemanticMatch.EXACT,
        period,
        SemanticMatch.EXACT,
        denominator,
        SemanticMatch.EXACT,
    )


def _source_provenance() -> EvidenceProvenance:
    verified = SourceProof(ProofState.VERIFIED, "sha256:verified")
    return EvidenceProvenance(
        EvidenceKind.SOURCE_REPRODUCTION, verified, verified, verified
    )


def _independent_provenance() -> EvidenceProvenance:
    missing = SourceProof(ProofState.MISSING, None)
    return EvidenceProvenance(
        EvidenceKind.INDEPENDENT_RECALCULATION,
        missing,
        missing,
        missing,
        formula_proof="paper_text_and_table",
    )
