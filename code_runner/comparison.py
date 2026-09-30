from decimal import Decimal
from typing import assert_never

from code_runner.models import (
    ComparisonMode,
    ComparisonRequest,
    EvidenceKind,
    NumericValue,
    ReviewResult,
    ReviewStatus,
    ThresholdOperator,
    ToleranceUnit,
)
from code_runner.numeric import (
    CanonicalValue,
    convert_to_unit,
    normalize,
    relative_difference,
    round_report_value,
)


def compare_evidence(
    request: ComparisonRequest, evidence: NumericValue
) -> ReviewResult:
    report_evidence = convert_to_unit(evidence, request.claim.value.unit)
    if report_evidence is None:
        return _result(ReviewStatus.NOT_COMPARABLE, "UNIT_DIMENSION_MISMATCH")
    rounded_evidence = round_report_value(
        report_evidence, request.tolerance.rounding_digits
    )
    provenance = request.execution.provenance
    if provenance is None:
        return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "EVIDENCE_PROVENANCE_MISSING")
    match provenance.kind:
        case EvidenceKind.SOURCE_REPRODUCTION:
            return _compare_reproduction(request, report_evidence, rounded_evidence)
        case EvidenceKind.INDEPENDENT_RECALCULATION:
            return _human_result(
                request, report_evidence, rounded_evidence, "INDEPENDENT_RECALCULATION"
            )
        case EvidenceKind.ARITHMETIC_CHECK:
            return _human_result(
                request, report_evidence, rounded_evidence, "ARITHMETIC_CHECK"
            )
        case unreachable:
            assert_never(unreachable)


def _compare_reproduction(
    request: ComparisonRequest, report: NumericValue, rounded: NumericValue
) -> ReviewResult:
    match request.claim.comparison_mode:
        case ComparisonMode.EXACT_VALUE:
            return _compare_value(request, report, report)
        case ComparisonMode.ROUNDED_INTERVAL:
            return _compare_value(request, report, rounded)
        case ComparisonMode.THRESHOLD:
            return _compare_threshold(request, report, rounded)
        case unreachable:
            assert_never(unreachable)


def _compare_value(
    request: ComparisonRequest, report: NumericValue, compared: NumericValue
) -> ReviewResult:
    claim = normalize(request.claim.value)
    evidence = normalize(compared)
    difference = abs(claim.amount - evidence.amount)
    relative = relative_difference(claim.amount, difference)
    absolute_ok = _within_absolute(request, difference, compared)
    relative_ok = (
        request.tolerance.relative is not None
        and relative is not None
        and relative <= request.tolerance.relative
    )
    if absolute_ok or relative_ok:
        return _comparison_result(
            ReviewStatus.MATCH,
            "VALUE_WITHIN_TOLERANCE",
            claim,
            evidence,
            difference,
            relative,
            report,
            compared,
        )
    return _comparison_result(
        ReviewStatus.MISMATCH,
        "VALUE_OUTSIDE_TOLERANCE",
        claim,
        evidence,
        difference,
        relative,
        report,
        compared,
    )


def _compare_threshold(
    request: ComparisonRequest, report: NumericValue, rounded: NumericValue
) -> ReviewResult:
    threshold = request.claim.threshold
    if threshold is None:
        return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "THRESHOLD_POLICY_MISSING")
    bound = convert_to_unit(threshold.value, report.unit)
    if bound is None:
        return _result(ReviewStatus.NOT_COMPARABLE, "THRESHOLD_UNIT_MISMATCH")
    match threshold.operator:
        case ThresholdOperator.LESS_THAN:
            passes = report.amount < bound.amount
        case ThresholdOperator.LESS_THAN_OR_EQUAL:
            passes = report.amount <= bound.amount
        case ThresholdOperator.GREATER_THAN:
            passes = report.amount > bound.amount
        case ThresholdOperator.GREATER_THAN_OR_EQUAL:
            passes = report.amount >= bound.amount
        case unreachable:
            assert_never(unreachable)
    status = ReviewStatus.MATCH if passes else ReviewStatus.MISMATCH
    code = "THRESHOLD_SATISFIED" if passes else "THRESHOLD_NOT_SATISFIED"
    return _comparison_result(
        status,
        code,
        normalize(request.claim.value),
        normalize(rounded),
        None,
        None,
        report,
        rounded,
    )


def _human_result(
    request: ComparisonRequest, report: NumericValue, rounded: NumericValue, code: str
) -> ReviewResult:
    provenance = request.execution.provenance
    if provenance is None:
        return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "EVIDENCE_PROVENANCE_MISSING")
    default = (
        "독립 재계산 — 원본 재현 아님"
        if provenance.kind is EvidenceKind.INDEPENDENT_RECALCULATION
        else "산술 검산 — 원본 재현 아님"
    )
    disclosure = (
        default
        if provenance.disclosure is None
        else f"{default}. {provenance.disclosure}"
    )
    return _result(ReviewStatus.NEEDS_HUMAN_REVIEW, code, report, rounded, disclosure)


def _within_absolute(
    request: ComparisonRequest, canonical_difference: Decimal, compared: NumericValue
) -> bool:
    match request.tolerance.absolute_unit:
        case ToleranceUnit.CANONICAL:
            return canonical_difference <= request.tolerance.absolute
        case ToleranceUnit.REPORT:
            return (
                abs(request.claim.value.amount - compared.amount)
                <= request.tolerance.absolute
            )
        case unreachable:
            assert_never(unreachable)


def _comparison_result(
    status: ReviewStatus,
    code: str,
    claim: CanonicalValue,
    evidence: CanonicalValue,
    difference: Decimal | None,
    relative: Decimal | None,
    report: NumericValue,
    rounded: NumericValue,
) -> ReviewResult:
    return ReviewResult(
        status,
        (code,),
        NumericValue(claim.amount, claim.unit),
        NumericValue(evidence.amount, evidence.unit),
        difference,
        relative,
        evidence_in_report_unit=report,
        rounded_evidence_in_report_unit=rounded,
    )


def _result(
    status: ReviewStatus,
    code: str,
    report: NumericValue | None = None,
    rounded: NumericValue | None = None,
    disclosure: str | None = None,
) -> ReviewResult:
    normalized_report = (
        None
        if report is None
        else NumericValue(normalize(report).amount, normalize(report).unit)
    )
    normalized_rounded = (
        None
        if rounded is None
        else NumericValue(normalize(rounded).amount, normalize(rounded).unit)
    )
    return ReviewResult(
        status,
        (code,),
        normalized_report,
        normalized_rounded,
        None,
        None,
        evidence_in_report_unit=report,
        rounded_evidence_in_report_unit=rounded,
        disclosure=disclosure,
    )
