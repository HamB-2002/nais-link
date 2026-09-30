from dataclasses import replace
from typing import assert_never

from code_runner.models import ReviewResult, ReviewStatus, SemanticMatch
from code_runner.triple_models import (
    BlockDecision,
    CheckResult,
    CheckStatus,
    CodeDataContract,
    DataContract,
    TripleComparisonRequest,
    TripleReviewResult,
)
from code_runner.workflow import evaluate


def evaluate_triple(request: TripleComparisonRequest) -> TripleReviewResult:
    report_data_check = _report_data_check(request.data)
    code_data_check = _code_data_check(request.code_data, request.data)
    match report_data_check.status:
        case CheckStatus.MISMATCH:
            return _blocked_result(
                BlockDecision(ReviewStatus.NOT_COMPARABLE, report_data_check),
                report_data_check,
                code_data_check,
            )
        case CheckStatus.UNKNOWN:
            return _blocked_result(
                BlockDecision(ReviewStatus.NEEDS_HUMAN_REVIEW, report_data_check),
                report_data_check,
                code_data_check,
            )
        case CheckStatus.PASS:
            return _after_report_data(request, report_data_check, code_data_check)
        case unreachable:
            assert_never(unreachable)


def _after_report_data(
    request: TripleComparisonRequest,
    report_data_check: CheckResult,
    code_data_check: CheckResult,
) -> TripleReviewResult:
    match code_data_check.status:
        case CheckStatus.MISMATCH:
            return _blocked_result(
                BlockDecision(ReviewStatus.EVIDENCE_INCOMPLETE, code_data_check),
                report_data_check,
                code_data_check,
            )
        case CheckStatus.UNKNOWN:
            return _blocked_result(
                BlockDecision(ReviewStatus.NEEDS_HUMAN_REVIEW, code_data_check),
                report_data_check,
                code_data_check,
            )
        case CheckStatus.PASS:
            review = evaluate(request.comparison)
            return TripleReviewResult(
                _report_code_review(review),
                report_data_check,
                code_data_check,
                _report_code_check(review),
                _next_action(review.status),
            )
        case unreachable:
            assert_never(unreachable)


def _report_data_check(contract: DataContract) -> CheckResult:
    input_match = contract.expected_inputs == contract.uploaded_inputs
    semantic = _semantic_state(contract.semantic_trace)
    match semantic:
        case SemanticMatch.MISMATCH:
            return CheckResult(CheckStatus.MISMATCH, ("REPORT_DATA_SEMANTIC_MISMATCH",))
        case SemanticMatch.UNKNOWN:
            return CheckResult(CheckStatus.UNKNOWN, ("REPORT_DATA_CONDITION_UNKNOWN",))
        case SemanticMatch.EXACT:
            if input_match:
                return CheckResult(CheckStatus.PASS, ())
            return CheckResult(CheckStatus.MISMATCH, ("REPORT_DATA_FILE_MISMATCH",))
        case unreachable:
            assert_never(unreachable)


def _code_data_check(code_data: CodeDataContract, data: DataContract) -> CheckResult:
    input_match = (
        code_data.declared_inputs == data.uploaded_inputs == code_data.observed_inputs
    )
    if not code_data.approved:
        return CheckResult(CheckStatus.MISMATCH, ("CODE_NOT_APPROVED",))
    if not input_match:
        return CheckResult(CheckStatus.MISMATCH, ("CODE_DATA_INPUT_MISMATCH",))
    return _code_conditions(code_data)


def _code_conditions(code_data: CodeDataContract) -> CheckResult:
    conditions = (code_data.schema_match, code_data.transform_match)
    semantic = _semantic_state(conditions)
    match semantic:
        case SemanticMatch.MISMATCH:
            return CheckResult(CheckStatus.MISMATCH, ("CODE_DATA_SCHEMA_MISMATCH",))
        case SemanticMatch.UNKNOWN:
            return CheckResult(CheckStatus.UNKNOWN, ("CODE_DATA_TRANSFORM_UNKNOWN",))
        case SemanticMatch.EXACT:
            return CheckResult(CheckStatus.PASS, ())
        case unreachable:
            assert_never(unreachable)


def _semantic_state(states: tuple[SemanticMatch, ...]) -> SemanticMatch:
    if SemanticMatch.MISMATCH in states:
        return SemanticMatch.MISMATCH
    if SemanticMatch.UNKNOWN in states:
        return SemanticMatch.UNKNOWN
    return SemanticMatch.EXACT


def _blocked_result(
    decision: BlockDecision,
    report_data_check: CheckResult,
    code_data_check: CheckResult,
) -> TripleReviewResult:
    review = ReviewResult(
        decision.status, decision.trigger.reason_codes, None, None, None, None
    )
    return TripleReviewResult(
        review,
        report_data_check,
        code_data_check,
        CheckResult(CheckStatus.UNKNOWN, decision.trigger.reason_codes),
        _next_action(decision.status),
    )


def _report_code_review(review: ReviewResult) -> ReviewResult:
    match review.status:
        case ReviewStatus.MATCH:
            return replace(review, reason_codes=("REPORT_CODE_VALUE_MATCH",))
        case ReviewStatus.MISMATCH:
            return replace(review, reason_codes=("REPORT_CODE_VALUE_MISMATCH",))
        case (
            ReviewStatus.NOT_COMPARABLE
            | ReviewStatus.EVIDENCE_INCOMPLETE
            | ReviewStatus.ISOLATION_UNAVAILABLE
            | ReviewStatus.EXECUTION_FAILED
            | ReviewStatus.NEEDS_HUMAN_REVIEW
        ):
            return review
        case unreachable:
            assert_never(unreachable)


def _report_code_check(review: ReviewResult) -> CheckResult:
    match review.status:
        case ReviewStatus.MATCH:
            return CheckResult(CheckStatus.PASS, ("REPORT_CODE_VALUE_MATCH",))
        case ReviewStatus.MISMATCH:
            return CheckResult(CheckStatus.MISMATCH, ("REPORT_CODE_VALUE_MISMATCH",))
        case (
            ReviewStatus.NOT_COMPARABLE
            | ReviewStatus.EVIDENCE_INCOMPLETE
            | ReviewStatus.ISOLATION_UNAVAILABLE
            | ReviewStatus.EXECUTION_FAILED
            | ReviewStatus.NEEDS_HUMAN_REVIEW
        ):
            return CheckResult(CheckStatus.UNKNOWN, review.reason_codes)
        case unreachable:
            assert_never(unreachable)


def _next_action(status: ReviewStatus) -> str:
    match status:
        case ReviewStatus.MATCH:
            return "세 근거가 일치합니다. 검토 기록을 보관하세요."
        case ReviewStatus.MISMATCH:
            return "보고서 표기값과 승인 코드 버전·분석 조건을 확인하세요."
        case ReviewStatus.NOT_COMPARABLE:
            return "보고서와 데이터의 기간·대상·분모·산식을 맞추세요."
        case ReviewStatus.EVIDENCE_INCOMPLETE:
            return "승인 코드와 실제 입력 데이터의 해시·경로를 확인하세요."
        case ReviewStatus.ISOLATION_UNAVAILABLE:
            return "Docker 격리 환경을 준비한 뒤 다시 실행하세요."
        case ReviewStatus.EXECUTION_FAILED:
            return "안전 실행 로그와 출력 계약을 확인하세요."
        case ReviewStatus.NEEDS_HUMAN_REVIEW:
            return "자동 판정 근거가 부족합니다. 검토자가 조건을 확인하세요."
        case unreachable:
            assert_never(unreachable)
