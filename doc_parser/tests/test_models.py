import pytest
from pydantic import ValidationError

from doc_parser.errors import ErrorCode
from doc_parser.models import (
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


def pdf_page() -> PageRef:
    return PageRef(start=1, end=1)


def pdf_paragraph() -> ParagraphBlock:
    return ParagraphBlock(
        id="b-000001",
        role=BlockRole.BODY,
        text="Revenue was 123.4.",
        order=0,
        page=pdf_page(),
        parse_status=ParseStatus.COMPLETE,
    )


def test_document_accepts_complete_pdf_paragraph() -> None:
    # Given: one complete paragraph with a physical page reference.
    block = pdf_paragraph()

    # When: a PDF document is created.
    document = Document(
        source_format=SourceFormat.PDF,
        status=DocumentStatus.COMPLETE,
        issues=[],
        blocks=[block],
    )

    # Then: the document retains the contract fields.
    assert document.blocks == [block]


def test_document_accepts_null_page_for_docx() -> None:
    # Given: a DOCX paragraph without a reliable physical page.
    block = ParagraphBlock(
        id="b-000001",
        role=BlockRole.BODY,
        text="Text",
        order=0,
        page=None,
        parse_status=ParseStatus.COMPLETE,
    )

    # When: a DOCX document is created.
    document = Document(
        source_format=SourceFormat.DOCX,
        status=DocumentStatus.COMPLETE,
        issues=[],
        blocks=[block],
    )

    # Then: its page remains unknown rather than inferred.
    assert document.blocks[0].page is None


def test_document_rejects_page_for_hwpx() -> None:
    # Given: an HWPX block with an inferred page.
    block = pdf_paragraph()

    # When: the HWPX document is validated.
    with pytest.raises(ValidationError):
        Document(
            source_format=SourceFormat.HWPX,
            status=DocumentStatus.COMPLETE,
            issues=[],
            blocks=[block],
        )

    # Then: the inferred page is rejected.


def test_document_rejects_missing_page_for_pdf() -> None:
    # Given: a PDF block without a physical page.
    block = ParagraphBlock(
        id="b-000001",
        role=BlockRole.BODY,
        text="Text",
        order=0,
        page=None,
        parse_status=ParseStatus.COMPLETE,
    )

    # When: the PDF document is validated.
    with pytest.raises(ValidationError):
        Document(
            source_format=SourceFormat.PDF,
            status=DocumentStatus.COMPLETE,
            issues=[],
            blocks=[block],
        )

    # Then: a missing PDF page is rejected.


def test_page_ref_rejects_reverse_range() -> None:
    # Given: a page range ending before it starts.

    # When: the reference is created.
    with pytest.raises(ValidationError):
        PageRef(start=2, end=1)

    # Then: the invalid range is rejected.


def test_document_rejects_duplicate_block_ids() -> None:
    # Given: two blocks sharing an id.
    first = pdf_paragraph()
    second = first.model_copy(update={"order": 1})

    # When: the document is created.
    with pytest.raises(ValidationError):
        Document(
            source_format=SourceFormat.PDF,
            status=DocumentStatus.COMPLETE,
            issues=[],
            blocks=[first, second],
        )

    # Then: duplicate source references are rejected.


def test_document_rejects_non_contiguous_order() -> None:
    # Given: a first block whose order does not begin at zero.
    block = pdf_paragraph().model_copy(update={"order": 1})

    # When: the document is created.
    with pytest.raises(ValidationError):
        Document(
            source_format=SourceFormat.PDF,
            status=DocumentStatus.COMPLETE,
            issues=[],
            blocks=[block],
        )

    # Then: non-contiguous traversal order is rejected.


def test_table_rejects_rows_that_do_not_match_text() -> None:
    # Given: a complete table with mismatched text.

    # When: the table is created.
    with pytest.raises(ValidationError):
        TableBlock(
            id="b-000001",
            role=BlockRole.BODY,
            text="wrong",
            rows=[["Metric", "Value"]],
            order=0,
            page=pdf_page(),
            parse_status=ParseStatus.COMPLETE,
        )

    # Then: the inconsistent representations are rejected.


def test_table_accepts_matching_rows_and_text() -> None:
    # Given: a simple rectangular table.
    rows = [["Metric", "Value"], ["Revenue", "123.4"]]

    # When: the table is created using its serialized rows.
    table = TableBlock(
        id="b-000001",
        role=BlockRole.BODY,
        text=serialize_rows(rows),
        rows=rows,
        order=0,
        page=pdf_page(),
        parse_status=ParseStatus.COMPLETE,
    )

    # Then: both representations are retained.
    assert table.rows == rows


def test_failed_block_requires_null_text() -> None:
    # Given: a failed block that incorrectly retains text.

    # When: the block is created.
    with pytest.raises(ValidationError):
        ParagraphBlock(
            id="b-000001",
            role=BlockRole.BODY,
            text="hidden failure",
            order=0,
            page=pdf_page(),
            parse_status=ParseStatus.FAILED,
        )

    # Then: failed extraction cannot masquerade as content.


def test_unknown_block_is_always_failed_with_null_text() -> None:
    # Given: an unknown block.

    # When: the block is created.
    block = UnknownBlock(id="b-000001", order=0, page=pdf_page())

    # Then: it records failed extraction without text.
    assert block.parse_status is ParseStatus.FAILED
    assert block.text is None


def test_document_rejects_issue_for_missing_block() -> None:
    # Given: a block-scoped issue referencing a missing id.
    issue = Issue(
        scope=IssueScope.BLOCK,
        block_id="b-999999",
        severity=IssueSeverity.WARNING,
        code=ErrorCode.TABLE_ROWS_UNAVAILABLE,
        message="Rows unavailable",
    )

    # When: the document is created.
    with pytest.raises(ValidationError):
        Document(
            source_format=SourceFormat.PDF,
            status=DocumentStatus.PARTIAL,
            issues=[issue],
            blocks=[pdf_paragraph()],
        )

    # Then: dangling issue references are rejected.
