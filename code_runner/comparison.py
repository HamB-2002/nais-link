from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import assert_never

from code_runner.models import (
    ComparisonRequest,
    ExecutionState,
    IsolationState,
    NumericValue,
    ReviewResult,
    ReviewStatus,
    SemanticMatch,
    Trace,
    TraceConfidence,
    Unit,
)


class Dimension(str, Enum):
    PERCENT = "percent"
    MULTIPLE = "multiple"
    MONEY = "money"
    TIME = "time"
    PERCENTAGE_POINT = "percentage_point"


class TraceState(str, Enum):
    EXACT = "exact"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CanonicalValue:
    amount: Decimal
    unit: Unit
    dimension: Dimension


def evaluate(request: ComparisonRequest) -> ReviewResult:
    if not request.execution.contract_complete:
        return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "EXECUTION_CONTRACT_INCOMPLETE")

    match request.execution.isolation:
        case IsolationState.UNAVAILABLE:
            return _result(ReviewStatus.ISOLATION_UNAVAILABLE, "DOCKER_NOT_AVAILABLE")
        case IsolationState.AVAILABLE:
            return _evaluate_execution(request)
        case unreachable:
            assert_never(unreachable)


def _evaluate_execution(request: ComparisonRequest) -> ReviewResult:
    match request.execution.state:
        case ExecutionState.NOT_STARTED:
            return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "EXECUTION_NOT_STARTED")
        case ExecutionState.FAILED:
            return _result(ReviewStatus.EXECUTION_FAILED, "EXECUTION_FAILED")
        case ExecutionState.COMPLETED:
            return _evaluate_completed_execution(request)
        case unreachable:
            assert_never(unreachable)


def _evaluate_completed_execution(request: ComparisonRequest) -> ReviewResult:
    evidence = request.execution.evidence
    if evidence is None:
        return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "OUTPUT_VALUE_MISSING")

    match request.trace.confidence:
        case TraceConfidence.LOW:
            return _result(ReviewStatus.NEEDS_HUMAN_REVIEW, "TRACE_CONFIDENCE_LOW")
        case TraceConfidence.HIGH:
            return _evaluate_trace(request, evidence)
        case unreachable:
            assert_never(unreachable)


def _evaluate_trace(request: ComparisonRequest, evidence: NumericValue) -> ReviewResult:
    match _trace_state(request.trace):
        case TraceState.MISMATCH:
            return _result(ReviewStatus.NOT_COMPARABLE, "SEMANTIC_CONDITION_MISMATCH")
        case TraceState.UNKNOWN:
            return _result(ReviewStatus.NEEDS_HUMAN_REVIEW, "SEMANTIC_CONDITION_UNKNOWN")
        case TraceState.EXACT:
            return _compare_values(request, evidence)
        case unreachable:
            assert_never(unreachable)


def _trace_state(trace: Trace) -> TraceState:
    has_unknown = False
    for condition in (
        trace.metric,
        trace.period,
        trace.population,
        trace.denominator,
        trace.formula,
    ):
        match condition:
            case SemanticMatch.MISMATCH:
                return TraceState.MISMATCH
            case SemanticMatch.UNKNOWN:
                has_unknown = True
            case SemanticMatch.EXACT:
                continue
            case unreachable:
                assert_never(unreachable)
    if has_unknown:
        return TraceState.UNKNOWN
    return TraceState.EXACT


def _compare_values(request: ComparisonRequest, evidence: NumericValue) -> ReviewResult:
    claim_value = _normalize(request.claim.value)
    evidence_value = _normalize(evidence)
    match (claim_value.dimension, evidence_value.dimension):
        case (Dimension.PERCENT, Dimension.PERCENT):
            return _compare_same_dimension(request, claim_value, evidence_value)
        case (Dimension.MULTIPLE, Dimension.MULTIPLE):
            return _compare_same_dimension(request, claim_value, evidence_value)
        case (Dimension.MONEY, Dimension.MONEY):
            return _compare_same_dimension(request, claim_value, evidence_value)
        case (Dimension.TIME, Dimension.TIME):
            return _compare_same_dimension(request, claim_value, evidence_value)
        case (Dimension.PERCENTAGE_POINT, Dimension.PERCENTAGE_POINT):
            return _compare_same_dimension(request, claim_value, evidence_value)
        case _:
            return _result(
                ReviewStatus.NOT_COMPARABLE,
                "UNIT_DIMENSION_MISMATCH",
                claim_value,
                evidence_value,
            )


def _compare_same_dimension(
    request: ComparisonRequest,
    claim_value: CanonicalValue,
    evidence_value: CanonicalValue,
) -> ReviewResult:
    rounded_evidence = _round(evidence_value.amount, request.tolerance.rounding_digits)
    absolute_difference = abs(claim_value.amount - rounded_evidence)
    relative_difference = _relative_difference(claim_value.amount, absolute_difference)
    within_absolute = absolute_difference <= request.tolerance.absolute
    within_relative = _within_relative_tolerance(
        relative_difference,
        request.tolerance.relative,
    )
    status = ReviewStatus.MATCH if within_absolute or within_relative else ReviewStatus.MISMATCH
    reason_code = "VALUE_WITHIN_TOLERANCE" if status is ReviewStatus.MATCH else "VALUE_OUTSIDE_TOLERANCE"
    return ReviewResult(
        status=status,
        reason_codes=(reason_code,),
        normalized_claim=NumericValue(claim_value.amount, claim_value.unit),
        normalized_evidence=NumericValue(rounded_evidence, evidence_value.unit),
        absolute_difference=absolute_difference,
        relative_difference=relative_difference,
    )


def _normalize(value: NumericValue) -> CanonicalValue:
    match value.unit:
        case Unit.PERCENT:
            return CanonicalValue(value.amount, Unit.PERCENT, Dimension.PERCENT)
        case Unit.RATIO:
            return CanonicalValue(value.amount * Decimal(100), Unit.PERCENT, Dimension.PERCENT)
        case Unit.MULTIPLE:
            return CanonicalValue(value.amount, Unit.MULTIPLE, Dimension.MULTIPLE)
        case Unit.WON:
            return CanonicalValue(value.amount / Decimal(1000000), Unit.MILLION_WON, Dimension.MONEY)
        case Unit.MILLION_WON:
            return CanonicalValue(value.amount, Unit.MILLION_WON, Dimension.MONEY)
        case Unit.HUNDRED_MILLION_WON:
            return CanonicalValue(value.amount * Decimal(100), Unit.MILLION_WON, Dimension.MONEY)
        case Unit.MILLISECOND:
            return CanonicalValue(value.amount / Decimal(1000), Unit.SECOND, Dimension.TIME)
        case Unit.SECOND:
            return CanonicalValue(value.amount, Unit.SECOND, Dimension.TIME)
        case Unit.PERCENTAGE_POINT:
            return CanonicalValue(value.amount, Unit.PERCENTAGE_POINT, Dimension.PERCENTAGE_POINT)
        case unreachable:
            assert_never(unreachable)


def _round(value: Decimal, digits: int) -> Decimal:
    quantum = Decimal(1).scaleb(-digits)
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def _relative_difference(claim: Decimal, absolute_difference: Decimal) -> Decimal | None:
    if claim == Decimal(0):
        return None
    return absolute_difference / abs(claim)


def _within_relative_tolerance(
    relative_difference: Decimal | None,
    tolerance: Decimal | None,
) -> bool:
    if relative_difference is None or tolerance is None:
        return False
    return relative_difference <= tolerance


def _result(
    status: ReviewStatus,
    reason_code: str,
    claim: CanonicalValue | None = None,
    evidence: CanonicalValue | None = None,
) -> ReviewResult:
    normalized_claim = None if claim is None else NumericValue(claim.amount, claim.unit)
    normalized_evidence = None if evidence is None else NumericValue(evidence.amount, evidence.unit)
    return ReviewResult(
        status=status,
        reason_codes=(reason_code,),
        normalized_claim=normalized_claim,
        normalized_evidence=normalized_evidence,
        absolute_difference=None,
        relative_difference=None,
    )
