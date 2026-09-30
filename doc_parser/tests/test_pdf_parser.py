from pathlib import Path

import pytest
from pdfminer.pdfdocument import PDFPasswordIncorrect

import doc_parser.pdf_parser as pdf_parser
from doc_parser.errors import ErrorCode
from doc_parser.models import ParseStatus, SourceFormat
from doc_parser.normalize import RawParagraph, RawTable, RawUnknown, normalize_document
from doc_parser.pdf_parser import PdfParseError, parse_pdf


def _write_pdf(path: Path, page_streams: list[bytes]) -> Path:
    page_ids = range(3, 3 + len(page_streams))
    font_id = 3 + len(page_streams)
    content_ids = range(font_id + 1, font_id + 1 + len(page_streams))
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {len(page_streams)} >>".encode(),
    ]
    objects.extend(
        (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {content_id} 0 R >>".encode()
            for content_id in content_ids
        )
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    objects.extend(
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"
        for stream in page_streams
    )
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id, content in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{object_id} 0 obj\n".encode())
        payload.extend(content)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    payload.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    payload.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    path.write_bytes(payload)
    return path


def _simple_table_pdf() -> bytes:
    return b"\n".join(
        (
            b"BT /F1 12 Tf 72 720 Td (Before 1,248 87.3% p < 0.05 3.14 \\261 0.21) Tj ET",
            b"72 650 m 272 650 l S 72 620 m 272 620 l S 72 590 m 272 590 l S",
            b"72 590 m 72 650 l S 172 590 m 172 650 l S 272 590 m 272 650 l S",
            b"BT /F1 12 Tf 80 630 Td (Metric) Tj ET BT /F1 12 Tf 180 630 Td (Value) Tj ET",
            b"BT /F1 12 Tf 80 600 Td (Mean) Tj ET BT /F1 12 Tf 180 600 Td (15) Tj ET",
            b"BT /F1 12 Tf 72 540 Td (After) Tj ET",
        )
    )


def _complex_table_pdf() -> bytes:
    return b"\n".join(
        (
            b"72 650 m 272 650 l S 72 620 m 272 620 l S 72 590 m 272 590 l S",
            b"72 590 m 72 650 l S 172 590 m 172 620 l S 272 590 m 272 650 l S",
            b"BT /F1 12 Tf 80 630 Td (Merged 87.3%) Tj ET",
            b"BT /F1 12 Tf 80 600 Td (p < 0.05) Tj ET BT /F1 12 Tf 180 600 Td (3.14 \\261 0.21) Tj ET",
        )
    )


def test_parse_pdf_preserves_pages_order_and_simple_table(tmp_path: Path) -> None:
    # Given: a two-page text PDF with one ruled simple table.
    source = _write_pdf(tmp_path / "simple.pdf", [_simple_table_pdf(), b"BT /F1 12 Tf 72 720 Td (Second page) Tj ET"])

    # When: the PDF is parsed and normalized.
    document = normalize_document(SourceFormat.PDF, parse_pdf(source))

    # Then: pages, table rows, and source numeric expressions remain available.
    assert [block.page.start for block in document.blocks if block.page is not None] == [1, 1, 2]
    assert document.blocks[1].rows == [["Metric", "Value"], ["Mean", "15"]]
    assert "1,248" in document.blocks[0].text
    assert "87.3%" in document.blocks[0].text
    assert "p < 0.05" in document.blocks[0].text
    assert "3.14 ± 0.21" in document.blocks[0].text


def test_parse_pdf_avoids_table_text_duplication(tmp_path: Path) -> None:
    # Given: a page with text before and after a ruled table.
    source = _write_pdf(tmp_path / "deduplication.pdf", [_simple_table_pdf()])

    # When: the PDF is parsed.
    candidates = parse_pdf(source)

    # Then: table text is absent from the paragraph candidate.
    paragraph = next(candidate for candidate in candidates if isinstance(candidate, RawParagraph))
    assert "Metric" not in paragraph.text


def test_parse_pdf_marks_merged_table_partial_with_text(tmp_path: Path) -> None:
    # Given: a ruled table whose merged header prevents a simple matrix.
    source = _write_pdf(tmp_path / "complex.pdf", [_complex_table_pdf()])

    # When: the PDF is parsed.
    table = next(candidate for candidate in parse_pdf(source) if isinstance(candidate, RawTable))

    # Then: its text survives while rows are withheld as partial.
    assert table.parse_status is ParseStatus.PARTIAL
    assert table.rows is None
    assert "87.3%" in table.text


def test_parse_pdf_marks_textless_page_unavailable(tmp_path: Path) -> None:
    # Given: a PDF page with no text layer.
    source = _write_pdf(tmp_path / "scan.pdf", [b""])

    # When: the page is parsed and normalized.
    document = normalize_document(SourceFormat.PDF, parse_pdf(source))

    # Then: OCR absence is recorded as a visible page-level failure.
    assert document.blocks[0].parse_status is ParseStatus.FAILED
    assert document.issues[0].code is ErrorCode.PDF_TEXT_UNAVAILABLE


def test_parse_pdf_rejects_damaged_container(tmp_path: Path) -> None:
    # Given: a non-PDF file carrying a PDF extension.
    source = tmp_path / "damaged.pdf"
    source.write_text("not a PDF", encoding="utf-8")

    # When: the file is parsed.
    with pytest.raises(PdfParseError) as raised:
        parse_pdf(source)

    # Then: container corruption has a distinct code.
    assert raised.value.code is ErrorCode.INVALID_CONTAINER


def test_parse_pdf_rejects_encrypted_document(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Given: pdfplumber reports a password-protected source at the I/O boundary.
    source = tmp_path / "encrypted.pdf"
    source.write_bytes(b"%PDF-1.4")

    # When: the file is parsed.
    def raise_password_error(_: Path) -> None:
        raise PDFPasswordIncorrect("password required")

    monkeypatch.setattr(pdf_parser.pdfplumber, "open", raise_password_error)
    with pytest.raises(PdfParseError) as raised:
        parse_pdf(source)

    # Then: encryption remains distinct from corruption.
    assert raised.value.code is ErrorCode.ENCRYPTED_DOCUMENT


def test_parse_pdf_reads_main_sample() -> None:
    # Given: a real PDF sample committed on the main branch.
    source = Path(__file__).resolve().parents[2] / "data/samples/sample-07/report.pdf"

    # When: the sample is parsed and normalized.
    document = normalize_document(SourceFormat.PDF, parse_pdf(source))

    # Then: all retained blocks carry physical pages and ordinary text is available.
    assert document.blocks
    assert all(block.page is not None for block in document.blocks)
    assert any(block.type == "paragraph" for block in document.blocks)
