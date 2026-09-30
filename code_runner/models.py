from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class Unit(str, Enum):
    PERCENT = "%"
    RATIO = "ratio"
    MULTIPLE = "배"
    WON = "원"
    MILLION_WON = "백만원"
    HUNDRED_MILLION_WON = "억원"
    MILLISECOND = "ms"
    SECOND = "s"
    PERCENTAGE_POINT = "%p"


class TraceConfidence(str, Enum):
    HIGH = "high"
    LOW = "low"


class SemanticMatch(str, Enum):
    EXACT = "exact"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


class IsolationState(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class ExecutionState(str, Enum):
    NOT_STARTED = "not_started"
    FAILED = "failed"
    COMPLETED = "completed"


class ReviewStatus(str, Enum):
    MATCH = "match"
    MISMATCH = "mismatch"
    NOT_COMPARABLE = "not_comparable"
    EVIDENCE_INCOMPLETE = "evidence_incomplete"
    ISOLATION_UNAVAILABLE = "isolation_unavailable"
    EXECUTION_FAILED = "execution_failed"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


@dataclass(frozen=True, slots=True)
class NumericValue:
    amount: Decimal
    unit: Unit


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    value: NumericValue
    metric: str
    period: str
    population: str
    denominator: str


@dataclass(frozen=True, slots=True)
class Trace:
    confidence: TraceConfidence
    metric: SemanticMatch
    period: SemanticMatch
    population: SemanticMatch
    denominator: SemanticMatch
    formula: SemanticMatch


@dataclass(frozen=True, slots=True)
class Execution:
    contract_complete: bool
    isolation: IsolationState
    state: ExecutionState
    evidence: NumericValue | None


@dataclass(frozen=True, slots=True)
class Tolerance:
    absolute: Decimal
    relative: Decimal | None
    rounding_digits: int


@dataclass(frozen=True, slots=True)
class ComparisonRequest:
    claim: Claim
    trace: Trace
    execution: Execution
    tolerance: Tolerance


@dataclass(frozen=True, slots=True)
class ReviewResult:
    status: ReviewStatus
    reason_codes: tuple[str, ...]
    normalized_claim: NumericValue | None
    normalized_evidence: NumericValue | None
    absolute_difference: Decimal | None
    relative_difference: Decimal | None
