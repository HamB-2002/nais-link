from doc_parser.errors import ErrorCode
from doc_parser.models import (
    BlockRole,
    DocumentStatus,
    PageRef,
    ParseStatus,
    SourceFormat,
)
from doc_parser.normalize import (
    RawParagraph,
    RawTable,
    RawUnknown,
    normalize_document,
    normalize_text,
)


def test_normalize_text_unifies_line_endings_without_collapsing_spaces() -> None:
    # Given: text with Windows and classic Mac line endings.
    text = "A  value\r\nB\rC"

    # When: text is normalized.
    normalized = normalize_text(text)

    # Then: line endings are consistent while interior spaces remain.
    assert normalized == "A  value\nB\nC"


def test_normalize_document_omits_empty_complete_paragraph() -> None:
    # Given: an empty paragraph before meaningful text.
    candidates = (
        RawParagraph(text=" \t\n"),
        RawParagraph(text="Revenue 123.4"),
    )

    # When: the candidates are normalized.
    document = normalize_document(SourceFormat.DOCX, candidates)

    # Then: only meaningful text receives an id and order.
    assert [block.id for block in document.blocks] == ["b-000001"]


def test_normalize_document_assigns_deterministic_ids_and_order() -> None:
    # Given: two non-empty paragraph candidates.
    candidates = (RawParagraph(text="First"), RawParagraph(text="Second"))

    # When: the candidates are normalized.
    document = normalize_document(SourceFormat.DOCX, candidates)

    # Then: ids and order follow the retained document sequence.
    assert [(block.id, block.order) for block in document.blocks] == [
        ("b-000001", 0),
        ("b-000002", 1),
    ]


def test_normalize_table_serializes_rows_to_text() -> None:
    # Given: a rectangular table with one numeric value.
    candidates = (
        RawTable(
            text=None,
            rows=(("Metric", "Value"), ("Revenue", "123.4")),
        ),
    )

    # When: the table is normalized.
    document = normalize_document(SourceFormat.DOCX, candidates)

    # Then: rows and text represent the same table.
    table = document.blocks[0]
    assert table.text == "Metric\tValue\nRevenue\t123.4"


def test_normalize_table_converts_null_cells_to_empty_strings() -> None:
    # Given: a table with a missing cell.
    candidates = (RawTable(text=None, rows=(("Metric", None),)),)

    # When: the table is normalized.
    document = normalize_document(SourceFormat.DOCX, candidates)

    # Then: the cell remains positionally present as an empty string.
    table = document.blocks[0]
    assert table.rows == [["Metric", ""]]


def test_normalize_table_marks_irregular_rows_partial() -> None:
    # Given: a table with rows of different widths.
    candidates = (RawTable(text=None, rows=(("A", "B"), ("1",))),)

    # When: the table is normalized.
    document = normalize_document(SourceFormat.DOCX, candidates)

    # Then: its text survives but cell rows are explicitly unavailable.
    table = document.blocks[0]
    assert table.parse_status is ParseStatus.PARTIAL
    assert table.rows is None
    assert document.issues[0].code is ErrorCode.TABLE_IRREGULAR_ROWS


def test_normalize_unknown_preserves_failure_and_issue() -> None:
    # Given: an unreadable source element.
    candidates = (
        RawUnknown(
            page=None,
            code=ErrorCode.UNSUPPORTED_ELEMENT,
            message="Unsupported drawing",
        ),
    )

    # When: the element is normalized.
    document = normalize_document(SourceFormat.DOCX, candidates)

    # Then: failure remains visible to later stages.
    block = document.blocks[0]
    assert block.text is None
    assert block.parse_status is ParseStatus.FAILED
    assert document.status is DocumentStatus.PARTIAL


def test_normalize_failed_paragraph_discards_raw_text() -> None:
    # Given: a failed paragraph candidate with stale raw text.
    candidates = (
        RawParagraph(text="stale", parse_status=ParseStatus.FAILED),
    )

    # When: the candidate is normalized.
    document = normalize_document(SourceFormat.DOCX, candidates)

    # Then: failed extraction cannot expose the stale text.
    assert document.blocks[0].text is None


def test_normalize_failed_table_discards_raw_rows() -> None:
    # Given: a failed table candidate retaining stale rows.
    candidates = (
        RawTable(
            text="stale",
            rows=(("stale",),),
            parse_status=ParseStatus.FAILED,
        ),
    )

    # When: the candidate is normalized.
    document = normalize_document(SourceFormat.DOCX, candidates)

    # Then: the result records failure without text or rows.
    table = document.blocks[0]
    assert table.text is None
    assert table.rows is None


def test_normalize_preserves_pdf_page_reference() -> None:
    # Given: a PDF paragraph on its physical second page.
    candidates = (
        RawParagraph(text="Text", page=PageRef(start=2, end=2)),
    )

    # When: the candidate is normalized.
    document = normalize_document(SourceFormat.PDF, candidates)

    # Then: the physical page is retained without inference.
    assert document.blocks[0].page == PageRef(start=2, end=2)


def test_normalize_preserves_numeric_expressions_in_paragraph() -> None:
    # Given: a paragraph containing distinct numeric representations.
    text = "1,248명; 87.3%; p < 0.05; 3.14 ± 0.21"

    # When: the paragraph is normalized.
    document = normalize_document(SourceFormat.DOCX, (RawParagraph(text=text),))

    # Then: every source representation remains unchanged.
    assert document.blocks[0].text == text


def test_normalize_preserves_numeric_expressions_in_table_rows() -> None:
    # Given: a table with numeric expressions and a cell-internal line break and tab.
    rows = (("1,248명", "87.3%"), ("p < 0.05\n3.14 ± 0.21", "A\tB"))

    # When: the table is normalized.
    document = normalize_document(SourceFormat.DOCX, (RawTable(text=None, rows=rows),))

    # Then: cell content remains available without replacing separators with spaces.
    assert document.blocks[0].rows == [list(row) for row in rows]


def test_normalize_preserves_partial_table_text() -> None:
    # Given: a partial table without reconstructable rows.
    text = "1,248명\t87.3%\np < 0.05\t3.14 ± 0.21"

    # When: the table is normalized.
    document = normalize_document(
        SourceFormat.DOCX,
        (RawTable(text=text, rows=None, parse_status=ParseStatus.PARTIAL),),
    )

    # Then: source table text remains available verbatim.
    assert document.blocks[0].text == text


def test_normalize_irregular_rows_preserves_richer_table_text() -> None:
    # Given: irregular rows and a richer source text representation.
    text = "표 1: 수치\n1,248명\t87.3%\np < 0.05\t3.14 ± 0.21"
    rows = (("1,248명", "87.3%"), ("p < 0.05",))

    # When: the table is normalized.
    document = normalize_document(SourceFormat.DOCX, (RawTable(text=text, rows=rows),))

    # Then: unreliable rows do not overwrite the richer source text.
    assert document.blocks[0].text == text
