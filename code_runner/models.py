from dataclasses import dataclass, field
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


class EvidenceKind(str, Enum):
    SOURCE_REPRODUCTION = "source_reproduction"
    INDEPENDENT_RECALCULATION = "independent_recalculation"
    ARITHMETIC_CHECK = "arithmetic_check"


class ProofState(str, Enum):
    VERIFIED = "verified"
    MISSING = "missing"
    UNKNOWN = "unknown"


class SourceKind(str, Enum):
    RESEARCH_RESULT = "research_result"
    PUBLISHED_EXAMPLE = "published_example"
    DERIVED_SUMMARY = "derived_summary"
    QUOTED_STATISTIC = "quoted_statistic"


class ComparisonMode(str, Enum):
    EXACT_VALUE = "exact_value"
    ROUNDED_INTERVAL = "rounded_interval"
    THRESHOLD = "threshold"


class ThresholdOperator(str, Enum):
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"


class ToleranceUnit(str, Enum):
    CANONICAL = "canonical"
    REPORT = "report"


@dataclass(frozen=True, slots=True)
class NumericValue:
    amount: Decimal
    unit: Unit


@dataclass(frozen=True, slots=True)
class SourceProof:
    state: ProofState
    reference: str | None


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    kind: EvidenceKind
    original_code: SourceProof
    original_data: SourceProof
    original_execution: SourceProof
    formula_proof: str | None = None
    disclosure: str | None = None


@dataclass(frozen=True, slots=True)
class SourceMetadata:
    source_kind: SourceKind
    research_result: bool | None
    file_sha256: str | None = None
    table_id: str | None = None
    row: str | None = None
    column: str | None = None
    cell_text: str | None = None
    context_text: str | None = None
    interpretation_scope: str | None = None


@dataclass(frozen=True, slots=True)
class Threshold:
    operator: ThresholdOperator
    value: NumericValue


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    value: NumericValue
    metric: str
    period: str
    population: str
    denominator: str
    raw_value: str | None = field(default=None, kw_only=True)
    source: SourceMetadata | None = field(default=None, kw_only=True)
    comparison_mode: ComparisonMode = field(
        default=ComparisonMode.ROUNDED_INTERVAL, kw_only=True
    )
    threshold: Threshold | None = field(default=None, kw_only=True)


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
    provenance: EvidenceProvenance | None = field(default=None, kw_only=True)


@dataclass(frozen=True, slots=True)
class Tolerance:
    absolute: Decimal
    relative: Decimal | None
    rounding_digits: int
    absolute_unit: ToleranceUnit = field(default=ToleranceUnit.CANONICAL, kw_only=True)


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
    evidence_in_report_unit: NumericValue | None = field(default=None, kw_only=True)
    rounded_evidence_in_report_unit: NumericValue | None = field(
        default=None, kw_only=True
    )
    disclosure: str | None = field(default=None, kw_only=True)
