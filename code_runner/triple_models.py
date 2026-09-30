from dataclasses import dataclass
from enum import Enum

from code_runner.models import (
    ComparisonRequest,
    ReviewResult,
    ReviewStatus,
    SemanticMatch,
)


class CheckStatus(str, Enum):
    PASS = "pass"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DataFile:
    path: str
    sha256: str
    row_count: int
    columns: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DataContract:
    expected_inputs: tuple[DataFile, ...]
    uploaded_inputs: tuple[DataFile, ...]
    semantic_trace: tuple[SemanticMatch, SemanticMatch, SemanticMatch, SemanticMatch]


@dataclass(frozen=True, slots=True)
class CodeDataContract:
    approved: bool
    declared_inputs: tuple[DataFile, ...]
    observed_inputs: tuple[DataFile, ...]
    schema_match: SemanticMatch
    transform_match: SemanticMatch


@dataclass(frozen=True, slots=True)
class TripleComparisonRequest:
    comparison: ComparisonRequest
    data: DataContract
    code_data: CodeDataContract


@dataclass(frozen=True, slots=True)
class CheckResult:
    status: CheckStatus
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BlockDecision:
    status: ReviewStatus
    trigger: CheckResult


@dataclass(frozen=True, slots=True)
class TripleReviewResult:
    review: ReviewResult
    report_data_check: CheckResult
    code_data_check: CheckResult
    report_code_check: CheckResult
    next_action: str
