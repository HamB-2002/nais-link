import pytest

from doc_parser.adapter import to_collector_blocks
from doc_parser.errors import ErrorCode
from doc_parser.models import BlockRole, PageRef, ParseStatus, SourceFormat
from doc_parser.normalize import (
    RawParagraph,
    RawTable,
    RawUnknown,
    normalize_document,
)


def test_adapter_emits_paragraph_and_caption_without_internal_fields() -> None:
    # Given: body and caption paragraphs in their source order.
    document = normalize_document(
        SourceFormat.DOCX,
        (
            RawParagraph(text="본문 1,248명"),
            RawParagraph(text="표 1. 87.3%", role=BlockRole.CAPTION),
        ),
    )

    # When: the document is adapted for numeric collection.
    blocks = to_collector_blocks(document)

    # Then: captions use their agreed external type without internal metadata.
    assert blocks == [
        {"type": "paragraph", "text": "본문 1,248명", "page": None, "order": 0},
        {"type": "caption", "text": "표 1. 87.3%", "page": None, "order": 1},
    ]


def test_adapter_preserves_table_rows_and_numeric_expressions() -> None:
    # Given: a complete table containing source numeric representations.
    rows = (("1,248명", "87.3%"), ("p < 0.05", "3.14 ± 0.21"))
    document = normalize_document(SourceFormat.DOCX, (RawTable(text=None, rows=rows),))

    # When: the table is adapted for numeric collection.
    blocks = to_collector_blocks(document)

    # Then: text and positional rows retain the original numeric expressions.
    assert blocks == [
        {
            "type": "table",
            "text": "1,248명\t87.3%\np < 0.05\t3.14 ± 0.21",
            "page": None,
            "order": 0,
            "rows": [list(row) for row in rows],
        }
    ]


def test_adapter_emits_partial_table_text_with_null_rows() -> None:
    # Given: a partial table whose cell matrix is unavailable.
    text = "p < 0.05\t3.14 ± 0.21"
    document = normalize_document(
        SourceFormat.HWPX,
        (RawTable(text=text, rows=None, parse_status=ParseStatus.PARTIAL),),
    )

    # When: the table is adapted for numeric collection.
    blocks = to_collector_blocks(document)

    # Then: the table text remains usable while unavailable rows remain null.
    assert blocks == [
        {"type": "table", "text": text, "page": None, "order": 0, "rows": None}
    ]


def test_adapter_uses_pdf_page_start() -> None:
    # Given: a PDF paragraph spanning physical pages two through three.
    document = normalize_document(
        SourceFormat.PDF,
        (RawParagraph(text="87.3%", page=PageRef(start=2, end=3)),),
    )

    # When: the paragraph is adapted for numeric collection.
    blocks = to_collector_blocks(document)

    # Then: the stable representative page is the physical start page.
    assert blocks[0]["page"] == 2


@pytest.mark.parametrize("source_format", (SourceFormat.DOCX, SourceFormat.HWPX))
def test_adapter_keeps_logical_format_page_null(source_format: SourceFormat) -> None:
    # Given: a logical-format paragraph with no reliable physical page.
    document = normalize_document(source_format, (RawParagraph(text="1,248명"),))

    # When: the paragraph is adapted for numeric collection.
    blocks = to_collector_blocks(document)

    # Then: the page remains null instead of being inferred.
    assert blocks[0]["page"] is None


def test_adapter_excludes_unknown_and_preserves_remaining_order() -> None:
    # Given: an unsupported element between two source paragraphs.
    document = normalize_document(
        SourceFormat.DOCX,
        (
            RawParagraph(text="Before"),
            RawUnknown(
                page=None,
                code=ErrorCode.UNSUPPORTED_ELEMENT,
                message="Unsupported drawing",
            ),
            RawParagraph(text="After"),
        ),
    )

    # When: the document is adapted for numeric collection.
    blocks = to_collector_blocks(document)

    # Then: unsupported content is excluded without renumbering source order.
    assert [block["order"] for block in blocks] == [0, 2]
