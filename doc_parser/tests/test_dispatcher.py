from pathlib import Path

import pytest
from docx import Document as WordDocument

from doc_parser.dispatcher import UnsupportedDocumentError, parse_document
from doc_parser.errors import ErrorCode


SAMPLE_ROOT = Path(__file__).resolve().parents[2] / "data/samples"


def test_parse_document_returns_docx_blocks_with_null_pages() -> None:
    # Given: a real DOCX sample committed on the main branch.
    source = SAMPLE_ROOT / "sample-10/report.docx"

    # When: the source is dispatched through the public entry point.
    blocks = parse_document(source)

    # Then: collector blocks retain DOCX's unknown-page policy.
    assert isinstance(blocks, list)
    assert blocks
    assert all(isinstance(block, dict) and block["page"] is None for block in blocks)


def test_parse_document_returns_hwpx_rows_and_source_numbers() -> None:
    # Given: a real HWPX sample containing tables and source numeric expressions.
    source = SAMPLE_ROOT / "sample-10-hwpx/report.hwpx"

    # When: the source is dispatched through the public entry point.
    blocks = parse_document(source)
    text = "\n".join(block["text"] for block in blocks)

    # Then: HWPX table rows and exact source numbers remain available without pages.
    assert isinstance(blocks, list)
    assert any(block["type"] == "table" and block["rows"] is not None for block in blocks)
    assert all(block["page"] is None for block in blocks)
    assert all(value in text for value in ("1,488개", "26.5%", "97.78%"))


def test_parse_document_returns_pdf_blocks_with_physical_pages_and_rows() -> None:
    # Given: a real PDF sample containing text and ruled tables.
    source = SAMPLE_ROOT / "sample-07/report.pdf"

    # When: the source is dispatched through the public entry point.
    blocks = parse_document(source)

    # Then: PDF pages become integers and simple tables expose rows.
    assert isinstance(blocks, list)
    assert all(isinstance(block["page"], int) for block in blocks)
    assert any(block["type"] == "table" and block["rows"] is not None for block in blocks)


def test_parse_document_converts_caption_to_external_type(tmp_path: Path) -> None:
    # Given: a DOCX paragraph using Word's built-in Caption style.
    source = tmp_path / "caption.docx"
    document = WordDocument()
    document.add_paragraph("Table 1. 87.3%", style="Caption")
    document.save(source)

    # When: the DOCX is dispatched through the public entry point.
    blocks = parse_document(source)

    # Then: the caption is labeled for the numeric collector.
    assert blocks == [
        {"type": "caption", "text": "Table 1. 87.3%", "page": None, "order": 0}
    ]


def test_parse_document_rejects_unsupported_extension(tmp_path: Path) -> None:
    # Given: a source with no supported document extension.
    source = tmp_path / "report.txt"

    # When: the source is dispatched.
    with pytest.raises(UnsupportedDocumentError) as raised:
        parse_document(source)

    # Then: the caller receives the standard unsupported-format code.
    assert raised.value.code is ErrorCode.UNSUPPORTED_FORMAT
