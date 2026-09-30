from dataclasses import dataclass
from decimal import Decimal

from code_runner.models import (
    Claim,
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
    Tolerance,
    Trace,
    TraceConfidence,
    Unit,
)
from code_runner.triple_models import (
    CodeDataContract,
    DataContract,
    DataFile,
    TripleComparisonRequest,
)
from code_runner.triple_workflow import evaluate_triple


def test_evaluate_triple_returns_match_when_all_three_evidence_legs_agree() -> None:
    # Given: 보고서 조건, 업로드 데이터, 승인 코드 입력이 모두 같은 재현 요청
    request = _fixture().request(_Scenario())

    # When: 삼중 대조를 실행하면
    result = evaluate_triple(request)

    # Then: 보고서-코드 값까지 일치로 반환한다.
    assert result.review.status is ReviewStatus.MATCH


def test_evaluate_triple_blocks_match_when_code_reads_a_different_data_file() -> None:
    # Given: 승인 코드는 있으나 실제 읽은 파일의 해시가 다른 요청
    wrong_file = DataFile(
        "data/other.csv", "sha256:other", 10, ("method", "latency_ms")
    )
    request = _fixture().request(_Scenario(observed_inputs=(wrong_file,)))

    # When: 삼중 대조를 실행하면
    result = evaluate_triple(request)

    # Then: 우연히 같은 값이어도 데이터 입력 불일치로 보류한다.
    assert result.review.reason_codes == ("CODE_DATA_INPUT_MISMATCH",)


def test_evaluate_triple_prioritizes_report_data_semantics_before_execution_value() -> (
    None
):
    # Given: 실행값은 같지만 보고서와 데이터의 기간이 다른 요청
    scenario = _Scenario(
        report_trace=(
            SemanticMatch.EXACT,
            SemanticMatch.MISMATCH,
            SemanticMatch.EXACT,
            SemanticMatch.EXACT,
        )
    )
    request = _fixture().request(scenario)

    # When: 삼중 대조를 실행하면
    result = evaluate_triple(request)

    # Then: 수치 일치가 아닌 비교 불가를 반환한다.
    assert result.review.status is ReviewStatus.NOT_COMPARABLE


def test_evaluate_triple_returns_human_review_when_code_transform_is_unknown() -> None:
    # Given: 입력 파일은 같지만 코드의 필터·집계 조건이 불명확한 요청
    request = _fixture().request(_Scenario(transform_match=SemanticMatch.UNKNOWN))

    # When: 삼중 대조를 실행하면
    result = evaluate_triple(request)

    # Then: 값 비교 전에 사람 검토를 요구한다.
    assert result.review.status is ReviewStatus.NEEDS_HUMAN_REVIEW


def test_evaluate_triple_preserves_schema_mismatch_reason() -> None:
    # Given: 입력 파일은 같지만 코드가 기대하는 데이터 스키마가 다른 요청
    request = _fixture().request(_Scenario(schema_match=SemanticMatch.MISMATCH))

    # When: 삼중 대조를 실행하면
    result = evaluate_triple(request)

    # Then: 일반 입력 불일치로 뭉개지지 않고 스키마 원인을 보존한다.
    assert result.review.reason_codes == ("CODE_DATA_SCHEMA_MISMATCH",)


def test_evaluate_triple_returns_value_mismatch_after_all_provenance_checks_pass() -> (
    None
):
    # Given: 세 근거는 같지만 보고서 수치와 다른 원본 재현값
    request = _fixture().request(
        _Scenario(evidence=NumericValue(Decimal("2.4"), Unit.MULTIPLE))
    )

    # When: 삼중 대조를 실행하면
    result = evaluate_triple(request)

    # Then: 원인을 보고서-코드 값 불일치로 특정한다.
    assert result.review.reason_codes == ("REPORT_CODE_VALUE_MISMATCH",)


@dataclass(frozen=True, slots=True)
class _Scenario:
    evidence: NumericValue | None = None
    observed_inputs: tuple[DataFile, ...] | None = None
    report_trace: tuple[SemanticMatch, SemanticMatch, SemanticMatch, SemanticMatch] = (
        SemanticMatch.EXACT,
        SemanticMatch.EXACT,
        SemanticMatch.EXACT,
        SemanticMatch.EXACT,
    )
    transform_match: SemanticMatch = SemanticMatch.EXACT
    schema_match: SemanticMatch = SemanticMatch.EXACT


class _Fixture:
    def __init__(self) -> None:
        self.data_file = DataFile(
            "data/benchmark.csv", "sha256:benchmark", 10, ("method", "latency_ms")
        )

    def request(self, scenario: _Scenario) -> TripleComparisonRequest:
        input_files = (
            (self.data_file,)
            if scenario.observed_inputs is None
            else scenario.observed_inputs
        )
        evidence = (
            NumericValue(Decimal("2.7"), Unit.MULTIPLE)
            if scenario.evidence is None
            else scenario.evidence
        )
        return TripleComparisonRequest(
            _comparison_request(evidence),
            DataContract((self.data_file,), (self.data_file,), scenario.report_trace),
            CodeDataContract(
                True,
                (self.data_file,),
                input_files,
                scenario.schema_match,
                scenario.transform_match,
            ),
        )


def _fixture() -> _Fixture:
    return _Fixture()


def _comparison_request(evidence: NumericValue) -> ComparisonRequest:
    proof = SourceProof(ProofState.VERIFIED, "sha256:verified")
    provenance = EvidenceProvenance(
        EvidenceKind.SOURCE_REPRODUCTION, proof, proof, proof
    )
    claim = Claim(
        "C-042",
        NumericValue(Decimal("2.7"), Unit.MULTIPLE),
        "처리 속도 개선 배수",
        "2025년 실험",
        "시험 데이터셋 A",
        "기존 방법 평균 처리 시간",
    )
    trace = Trace(
        TraceConfidence.HIGH,
        SemanticMatch.EXACT,
        SemanticMatch.EXACT,
        SemanticMatch.EXACT,
        SemanticMatch.EXACT,
        SemanticMatch.EXACT,
    )
    execution = Execution(
        True,
        IsolationState.AVAILABLE,
        ExecutionState.COMPLETED,
        evidence,
        provenance=provenance,
    )
    return ComparisonRequest(
        claim, trace, execution, Tolerance(Decimal("0.05"), None, 1)
    )
