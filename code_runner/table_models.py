from dataclasses import dataclass
from enum import Enum

from code_runner.models import (
    Execution,
    NumericValue,
    ReviewResult,
    ReviewStatus,
    SourceMetadata,
    Tolerance,
    TolerancePolicy,
)


class TablePairStatus(str, Enum):
    MATCHED = "matched"
    UNMATCHED = "unmatched"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class TableCoordinate:
    panel: str | None
    row_key: str
    column_path: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QuantitySemantics:
    metric: str | None
    period: str | None
    population: str | None
    denominator: str | None
    formula: str | None


@dataclass(frozen=True, slots=True)
class ReportTableCell:
    coordinate: TableCoordinate
    value: NumericValue
    raw_value: str
    semantics: QuantitySemantics
    source: SourceMetadata
    tolerance: Tolerance
    tolerance_policy: TolerancePolicy | None = None


@dataclass(frozen=True, slots=True)
class ExecutionTableCell:
    coordinate: TableCoordinate
    value: NumericValue
    semantics: QuantitySemantics
    execution: Execution
    output_locator: str


@dataclass(frozen=True, slots=True)
class ReportTableArtifact:
    table_id: str
    title: str
    cells: tuple[ReportTableCell, ...]


@dataclass(frozen=True, slots=True)
class ExecutionTableArtifact:
    table_id: str
    title: str
    cells: tuple[ExecutionTableCell, ...]
    run_id: str


@dataclass(frozen=True, slots=True)
class TableCandidate:
    report_table_id: str
    execution_table_id: str
    score: int
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CellComparison:
    report_coordinate: TableCoordinate
    execution_coordinate: TableCoordinate | None
    reported_value: NumericValue
    execution_value: NumericValue | None
    status: ReviewStatus
    reason_codes: tuple[str, ...]
    review: ReviewResult | None
    output_locator: str | None
    tolerance_policy: TolerancePolicy | None


@dataclass(frozen=True, slots=True)
class TableComparison:
    status: TablePairStatus
    report_table_id: str
    execution_table_id: str | None
    pairing_reasons: tuple[str, ...]
    cell_results: tuple[CellComparison, ...]
    unmatched_execution_cells: tuple[TableCoordinate, ...]


@dataclass(frozen=True, slots=True)
class TableReconciliationResult:
    comparisons: tuple[TableComparison, ...]
    unmatched_execution_tables: tuple[str, ...]
