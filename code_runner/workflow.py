from typing import assert_never

from code_runner.comparison import compare_evidence
from code_runner.models import (
    ComparisonRequest,
    EvidenceKind,
    ExecutionState,
    IsolationState,
    ProofState,
    ReviewResult,
    ReviewStatus,
    SemanticMatch,
    Trace,
    TraceConfidence,
)


def evaluate(request: ComparisonRequest) -> ReviewResult:
    if not request.execution.contract_complete:
        return _result(
            ReviewStatus.EVIDENCE_INCOMPLETE, "EXECUTION_CONTRACT_INCOMPLETE"
        )
    match request.execution.isolation:
        case IsolationState.UNAVAILABLE:
            return _result(ReviewStatus.ISOLATION_UNAVAILABLE, "DOCKER_NOT_AVAILABLE")
        case IsolationState.AVAILABLE:
            return _evaluate_trace(request)
        case unreachable:
            assert_never(unreachable)


def _evaluate_trace(request: ComparisonRequest) -> ReviewResult:
    semantic = _semantic_state(request.trace)
    if semantic is SemanticMatch.MISMATCH:
        return _result(ReviewStatus.NOT_COMPARABLE, "SEMANTIC_CONDITION_MISMATCH")
    if semantic is SemanticMatch.UNKNOWN:
        return _result(ReviewStatus.NEEDS_HUMAN_REVIEW, "SEMANTIC_CONDITION_UNKNOWN")
    if request.trace.confidence is TraceConfidence.LOW:
        return _result(ReviewStatus.NEEDS_HUMAN_REVIEW, "TRACE_CONFIDENCE_LOW")
    return _evaluate_provenance(request)


def _evaluate_provenance(request: ComparisonRequest) -> ReviewResult:
    provenance = request.execution.provenance
    if provenance is None:
        return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "EVIDENCE_PROVENANCE_MISSING")
    if (
        provenance.kind is EvidenceKind.SOURCE_REPRODUCTION
        and not _has_verified_original_proofs(request)
    ):
        return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "ORIGINAL_PROOFS_INCOMPLETE")
    return _evaluate_execution(request)


def _evaluate_execution(request: ComparisonRequest) -> ReviewResult:
    match request.execution.state:
        case ExecutionState.NOT_STARTED:
            return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "EXECUTION_NOT_STARTED")
        case ExecutionState.FAILED:
            return _result(ReviewStatus.EXECUTION_FAILED, "EXECUTION_FAILED")
        case ExecutionState.COMPLETED:
            evidence = request.execution.evidence
            if evidence is None:
                return _result(ReviewStatus.EVIDENCE_INCOMPLETE, "OUTPUT_VALUE_MISSING")
            return compare_evidence(request, evidence)
        case unreachable:
            assert_never(unreachable)


def _semantic_state(trace: Trace) -> SemanticMatch:
    states = (
        trace.metric,
        trace.period,
        trace.population,
        trace.denominator,
        trace.formula,
    )
    if SemanticMatch.MISMATCH in states:
        return SemanticMatch.MISMATCH
    if SemanticMatch.UNKNOWN in states:
        return SemanticMatch.UNKNOWN
    return SemanticMatch.EXACT


def _has_verified_original_proofs(request: ComparisonRequest) -> bool:
    provenance = request.execution.provenance
    if provenance is None:
        return False
    proofs = (
        provenance.original_code,
        provenance.original_data,
        provenance.original_execution,
    )
    return all(
        proof.state is ProofState.VERIFIED and bool(proof.reference) for proof in proofs
    )


def _result(status: ReviewStatus, code: str) -> ReviewResult:
    return ReviewResult(status, (code,), None, None, None, None)
