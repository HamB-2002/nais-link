from enum import StrEnum
from typing import Annotated, Literal, Self, assert_never

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from doc_parser.errors import ErrorCode


class SourceFormat(StrEnum):
    PDF = "pdf"
    DOCX = "docx"
    HWPX = "hwpx"


class DocumentStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    ENCRYPTED = "encrypted"
    UNSUPPORTED = "unsupported"


class BlockRole(StrEnum):
    BODY = "body"
    HEADING = "heading"
    CAPTION = "caption"
    HEADER = "header"
    FOOTER = "footer"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    UNKNOWN = "unknown"


class ParseStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"


class IssueScope(StrEnum):
    DOCUMENT = "document"
    BLOCK = "block"


class IssueSeverity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class PageRef(ContractModel):
    start: int = Field(ge=1)
    end: int = Field(ge=1)
    kind: Literal["physical"] = "physical"

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.end < self.start:
            raise PydanticCustomError(
                "invalid_page_range", "page end must not precede page start"
            )
        return self


class Issue(ContractModel):
    scope: IssueScope
    block_id: str | None = None
    severity: IssueSeverity
    code: ErrorCode
    message: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_scope_reference(self) -> Self:
        match self.scope:
            case IssueScope.DOCUMENT:
                if self.block_id is not None:
                    raise PydanticCustomError(
                        "document_issue_block_reference",
                        "document issues must not reference a block",
                    )
            case IssueScope.BLOCK:
                if self.block_id is None:
                    raise PydanticCustomError(
                        "block_issue_missing_reference",
                        "block issues must reference a block",
                    )
            case unreachable:
                assert_never(unreachable)
        return self


class BlockBase(ContractModel):
    id: str = Field(min_length=1)
    role: BlockRole
    text: str | None
    order: int = Field(ge=0)
    page: PageRef | None
    parse_status: ParseStatus

    @model_validator(mode="after")
    def validate_text_status(self) -> Self:
        match self.parse_status:
            case ParseStatus.COMPLETE | ParseStatus.PARTIAL:
                if self.text is None:
                    raise PydanticCustomError(
                        "missing_extracted_text",
                        "complete or partial blocks must contain text",
                    )
            case ParseStatus.FAILED:
                if self.text is not None:
                    raise PydanticCustomError(
                        "failed_block_text", "failed blocks must use null text"
                    )
            case unreachable:
                assert_never(unreachable)
        return self


class ParagraphBlock(BlockBase):
    type: Literal["paragraph"] = "paragraph"


def serialize_rows(rows: list[list[str]]) -> str:
    return "\n".join("\t".join(row) for row in rows)


class TableBlock(BlockBase):
    type: Literal["table"] = "table"
    rows: list[list[str]] | None

    @model_validator(mode="after")
    def validate_rows(self) -> Self:
        match self.parse_status:
            case ParseStatus.COMPLETE:
                if self.rows is None:
                    raise PydanticCustomError(
                        "complete_table_missing_rows",
                        "complete tables must contain rows",
                    )
            case ParseStatus.PARTIAL:
                pass
            case ParseStatus.FAILED:
                if self.rows is not None:
                    raise PydanticCustomError(
                        "failed_table_rows", "failed tables must use null rows"
                    )
            case unreachable:
                assert_never(unreachable)

        if self.rows is not None:
            widths = {len(row) for row in self.rows}
            if len(widths) > 1:
                raise PydanticCustomError(
                    "irregular_table_rows", "table rows must have a shared width"
                )
            if self.text != serialize_rows(self.rows):
                raise PydanticCustomError(
                    "table_text_rows_mismatch",
                    "table text must match the serialized rows",
                )
        return self


class UnknownBlock(BlockBase):
    type: Literal["unknown"] = "unknown"
    role: Literal[BlockRole.UNKNOWN] = BlockRole.UNKNOWN
    text: Literal[None] = None
    parse_status: Literal[ParseStatus.FAILED] = ParseStatus.FAILED


Block = Annotated[
    ParagraphBlock | TableBlock | UnknownBlock,
    Field(discriminator="type"),
]


class Document(ContractModel):
    schema_version: Literal["1.0"] = "1.0"
    source_format: SourceFormat
    status: DocumentStatus
    issues: list[Issue]
    blocks: list[Block]

    @model_validator(mode="after")
    def validate_contract(self) -> Self:
        self._validate_block_sequence()
        self._validate_issue_references()
        self._validate_page_policy()
        self._validate_status()
        return self

    def _validate_block_sequence(self) -> None:
        block_ids = [block.id for block in self.blocks]
        if len(block_ids) != len(set(block_ids)):
            raise PydanticCustomError(
                "duplicate_block_id", "document block ids must be unique"
            )

        orders = [block.order for block in self.blocks]
        if orders != list(range(len(self.blocks))):
            raise PydanticCustomError(
                "invalid_block_order", "block order must be contiguous from zero"
            )

    def _validate_issue_references(self) -> None:
        block_ids = {block.id for block in self.blocks}
        for issue in self.issues:
            match issue.scope:
                case IssueScope.DOCUMENT:
                    continue
                case IssueScope.BLOCK:
                    if issue.block_id not in block_ids:
                        raise PydanticCustomError(
                            "unknown_issue_block", "block issue must reference an existing block"
                        )
                case unreachable:
                    assert_never(unreachable)

    def _validate_page_policy(self) -> None:
        match self.source_format:
            case SourceFormat.PDF:
                if any(block.page is None for block in self.blocks):
                    raise PydanticCustomError(
                        "missing_pdf_page", "PDF blocks must have physical page references"
                    )
            case SourceFormat.DOCX | SourceFormat.HWPX:
                if any(block.page is not None for block in self.blocks):
                    raise PydanticCustomError(
                        "unexpected_logical_page",
                        "DOCX and HWPX blocks must use null pages",
                    )
            case unreachable:
                assert_never(unreachable)

    def _validate_status(self) -> None:
        match self.status:
            case DocumentStatus.COMPLETE:
                self._require_complete_blocks()
                self._reject_error_issues()
            case DocumentStatus.PARTIAL:
                if not self._has_incomplete_block() and not self.issues:
                    raise PydanticCustomError(
                        "unexplained_partial_document",
                        "partial documents require an issue or incomplete block",
                    )
            case DocumentStatus.FAILED | DocumentStatus.ENCRYPTED | DocumentStatus.UNSUPPORTED:
                if self.blocks:
                    raise PydanticCustomError(
                        "terminal_document_blocks",
                        "terminal document states must not contain blocks",
                    )
            case unreachable:
                assert_never(unreachable)

    def _require_complete_blocks(self) -> None:
        for block in self.blocks:
            match block.parse_status:
                case ParseStatus.COMPLETE:
                    continue
                case ParseStatus.PARTIAL | ParseStatus.FAILED:
                    raise PydanticCustomError(
                        "incomplete_complete_document",
                        "complete documents require complete blocks",
                    )
                case unreachable:
                    assert_never(unreachable)

    def _reject_error_issues(self) -> None:
        for issue in self.issues:
            match issue.severity:
                case IssueSeverity.WARNING:
                    continue
                case IssueSeverity.ERROR:
                    raise PydanticCustomError(
                        "error_in_complete_document",
                        "complete documents cannot contain error issues",
                    )
                case unreachable:
                    assert_never(unreachable)

    def _has_incomplete_block(self) -> bool:
        for block in self.blocks:
            match block.parse_status:
                case ParseStatus.COMPLETE:
                    continue
                case ParseStatus.PARTIAL | ParseStatus.FAILED:
                    return True
                case unreachable:
                    assert_never(unreachable)
        return False
