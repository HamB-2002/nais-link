from dataclasses import dataclass
from typing import assert_never
from unicodedata import normalize as unicode_normalize

from doc_parser.errors import ErrorCode
from doc_parser.models import (
    Block,
    BlockRole,
    Document,
    DocumentStatus,
    Issue,
    IssueScope,
    IssueSeverity,
    PageRef,
    ParagraphBlock,
    ParseStatus,
    SourceFormat,
    TableBlock,
    UnknownBlock,
    serialize_rows,
)


@dataclass(frozen=True, slots=True)
class RawParagraph:
    text: str | None
    role: BlockRole = BlockRole.BODY
    page: PageRef | None = None
    parse_status: ParseStatus = ParseStatus.COMPLETE


@dataclass(frozen=True, slots=True)
class RawTable:
    text: str | None
    rows: tuple[tuple[str | None, ...], ...] | None
    role: BlockRole = BlockRole.BODY
    page: PageRef | None = None
    parse_status: ParseStatus = ParseStatus.COMPLETE


@dataclass(frozen=True, slots=True)
class RawUnknown:
    page: PageRef | None
    code: ErrorCode
    message: str


RawBlock = RawParagraph | RawTable | RawUnknown


def normalize_text(text: str) -> str:
    return unicode_normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")


def normalize_document(
    source_format: SourceFormat, candidates: tuple[RawBlock, ...]
) -> Document:
    blocks: list[Block] = []
    issues: list[Issue] = []

    for candidate in candidates:
        block, issue = _normalize_candidate(candidate, len(blocks))
        if block is not None:
            blocks.append(block)
        if issue is not None:
            issues.append(issue)

    status = _document_status(blocks, issues)
    return Document(
        source_format=source_format,
        status=status,
        issues=issues,
        blocks=blocks,
    )


def _normalize_candidate(
    candidate: RawBlock, order: int
) -> tuple[Block | None, Issue | None]:
    block_id = f"b-{order + 1:06d}"
    match candidate:
        case RawParagraph(text=text, role=role, page=page, parse_status=parse_status):
            match parse_status:
                case ParseStatus.COMPLETE:
                    normalized_text = None if text is None else normalize_text(text)
                    if normalized_text is not None and normalized_text.strip() == "":
                        return None, None
                case ParseStatus.PARTIAL:
                    normalized_text = None if text is None else normalize_text(text)
                case ParseStatus.FAILED:
                    normalized_text = None
                case unreachable:
                    assert_never(unreachable)
            return (
                ParagraphBlock(
                    id=block_id,
                    role=role,
                    text=normalized_text,
                    order=order,
                    page=page,
                    parse_status=parse_status,
                ),
                None,
            )
        case RawTable(text=text, rows=rows, role=role, page=page, parse_status=parse_status):
            raw_table = RawTable(text, rows, role, page, parse_status)
            return _normalize_table(block_id, order, raw_table)
        case RawUnknown(page=page, code=code, message=message):
            return (
                UnknownBlock(id=block_id, order=order, page=page),
                Issue(
                    scope=IssueScope.BLOCK,
                    block_id=block_id,
                    severity=IssueSeverity.ERROR,
                    code=code,
                    message=message,
                ),
            )
        case unreachable:
            assert_never(unreachable)


def _normalize_table(
    block_id: str, order: int, table: RawTable
) -> tuple[Block, Issue | None]:
    match table.parse_status:
        case ParseStatus.FAILED:
            return _failed_table(block_id, order, table)
        case ParseStatus.COMPLETE | ParseStatus.PARTIAL:
            pass
        case unreachable:
            assert_never(unreachable)

    if table.rows is None:
        return _table_without_rows(block_id, order, table)

    normalized_rows = [
        [_normalize_cell(cell) for cell in row]
        for row in table.rows
    ]
    if len({len(row) for row in normalized_rows}) > 1:
        normalized_text = (
            normalize_text(table.text)
            if table.text is not None
            else serialize_rows(normalized_rows)
        )
        return (
            TableBlock(
                id=block_id,
                role=table.role,
                text=normalized_text,
                rows=None,
                order=order,
                page=table.page,
                parse_status=ParseStatus.PARTIAL,
            ),
            _table_issue(block_id, ErrorCode.TABLE_IRREGULAR_ROWS),
        )

    return (
        TableBlock(
            id=block_id,
            role=table.role,
            text=serialize_rows(normalized_rows),
            rows=normalized_rows,
            order=order,
            page=table.page,
            parse_status=table.parse_status,
        ),
        None,
    )


def _table_without_rows(
    block_id: str, order: int, table: RawTable
) -> tuple[Block, Issue | None]:
    normalized_text = None if table.text is None else normalize_text(table.text)
    match table.parse_status:
        case ParseStatus.COMPLETE:
            if normalized_text is None:
                return _failed_table(block_id, order, table)
            return (
                TableBlock(
                    id=block_id,
                    role=table.role,
                    text=normalized_text,
                    rows=None,
                    order=order,
                    page=table.page,
                    parse_status=ParseStatus.PARTIAL,
                ),
                _table_issue(block_id, ErrorCode.TABLE_ROWS_UNAVAILABLE),
            )
        case ParseStatus.PARTIAL:
            if normalized_text is None:
                return _failed_table(block_id, order, table)
            return (
                TableBlock(
                    id=block_id,
                    role=table.role,
                    text=normalized_text,
                    rows=None,
                    order=order,
                    page=table.page,
                    parse_status=ParseStatus.PARTIAL,
                ),
                _table_issue(block_id, ErrorCode.TABLE_ROWS_UNAVAILABLE),
            )
        case ParseStatus.FAILED:
            return _failed_table(block_id, order, table)
        case unreachable:
            assert_never(unreachable)


def _failed_table(
    block_id: str, order: int, table: RawTable
) -> tuple[Block, Issue]:
    return (
        TableBlock(
            id=block_id,
            role=table.role,
            text=None,
            rows=None,
            order=order,
            page=table.page,
            parse_status=ParseStatus.FAILED,
        ),
        _table_issue(block_id, ErrorCode.TEXT_EXTRACTION_FAILED),
    )


def _normalize_cell(cell: str | None) -> str:
    if cell is None:
        return ""
    return normalize_text(cell)


def _table_issue(block_id: str, code: ErrorCode) -> Issue:
    match code:
        case ErrorCode.TABLE_ROWS_UNAVAILABLE:
            message = "table text is available but rows could not be reconstructed"
        case ErrorCode.TABLE_IRREGULAR_ROWS:
            message = "table rows do not form a simple rectangular matrix"
        case ErrorCode.TEXT_EXTRACTION_FAILED:
            message = "table text could not be extracted"
        case unreachable:
            assert_never(unreachable)
    return Issue(
        scope=IssueScope.BLOCK,
        block_id=block_id,
        severity=IssueSeverity.WARNING,
        code=code,
        message=message,
    )


def _document_status(blocks: list[Block], issues: list[Issue]) -> DocumentStatus:
    if not blocks:
        return DocumentStatus.COMPLETE
    if issues:
        return DocumentStatus.PARTIAL
    for block in blocks:
        match block.parse_status:
            case ParseStatus.COMPLETE:
                continue
            case ParseStatus.PARTIAL | ParseStatus.FAILED:
                return DocumentStatus.PARTIAL
            case unreachable:
                assert_never(unreachable)
    return DocumentStatus.COMPLETE
