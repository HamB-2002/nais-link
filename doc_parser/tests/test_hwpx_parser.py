from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

import pytest

from doc_parser.errors import ErrorCode
from doc_parser.hwpx_parser import HwpxParseError, parse_hwpx
from doc_parser.models import BlockRole, ParseStatus, SourceFormat
from doc_parser.normalize import RawParagraph, RawTable, normalize_document


CONTAINER_XML = """<container><rootfiles><rootfile full-path=\"Contents/content.hpf\"/></rootfiles></container>"""
HEADER_XML = """<hh:head xmlns:hh=\"urn:head\"><hh:style id=\"h1\" name=\"Heading 1\"/><hh:style id=\"caption\" name=\"Caption\"/></hh:head>"""


def _content_hpf(section_items: tuple[tuple[str, str], ...], spine: tuple[str, ...]) -> str:
    manifest = "".join(
        f'<opf:item id="{item_id}" href="{href}"/>'
        for item_id, href in section_items
    )
    itemrefs = "".join(f'<opf:itemref idref="{item_id}"/>' for item_id in spine)
    return (
        '<opf:package xmlns:opf="urn:opf"><opf:manifest>'
        f"{manifest}"
        "</opf:manifest><opf:spine>"
        f"{itemrefs}"
        "</opf:spine></opf:package>"
    )


def _section_xml(body: str) -> str:
    return (
        '<hs:sec xmlns:hs="urn:section" xmlns:hp="urn:paragraph">'
        f"{body}"
        "</hs:sec>"
    )


def _write_hwpx(
    path: Path,
    sections: dict[str, str],
    spine: tuple[str, ...],
    mimetype: bytes = b"application/hwp+zip",
    include_header: bool = True,
    omitted_sections: frozenset[str] = frozenset(),
) -> Path:
    section_items = tuple((f"section-{index}", name) for index, name in enumerate(sections))
    with ZipFile(path, "w") as archive:
        archive.writestr("mimetype", mimetype, compress_type=ZIP_STORED)
        archive.writestr("META-INF/container.xml", CONTAINER_XML)
        archive.writestr("Contents/content.hpf", _content_hpf(section_items, spine))
        if include_header:
            archive.writestr("Contents/header.xml", HEADER_XML)
        for name, content in sections.items():
            if name not in omitted_sections:
                archive.writestr(f"Contents/{name}", content)
    return path


def test_parse_hwpx_uses_spine_order_for_sections(tmp_path: Path) -> None:
    # Given: section filenames whose lexical order differs from their spine order.
    source = _write_hwpx(
        tmp_path / "spine.hwpx",
        {
            "section-a.xml": _section_xml("<hp:p><hp:run><hp:t>Second</hp:t></hp:run></hp:p>"),
            "section-z.xml": _section_xml("<hp:p><hp:run><hp:t>First</hp:t></hp:run></hp:p>"),
        },
        ("section-1", "section-0"),
    )

    # When: the HWPX package is parsed.
    candidates = parse_hwpx(source)

    # Then: section content follows spine rather than filename order.
    assert [candidate.text for candidate in candidates] == ["First", "Second"]


def test_parse_hwpx_preserves_paragraph_table_paragraph_order(tmp_path: Path) -> None:
    # Given: a paragraph containing text, a simple table, and trailing text.
    table = """
    <hp:tbl><hp:tr><hp:tc><hp:subList><hp:p><hp:run><hp:t>Metric</hp:t></hp:run></hp:p></hp:subList></hp:tc>
    <hp:tc><hp:subList><hp:p><hp:run><hp:t>Value</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr></hp:tbl>
    """
    source = _write_hwpx(
        tmp_path / "order.hwpx",
        {"section.xml": _section_xml(f"<hp:p><hp:run><hp:t>Before</hp:t>{table}<hp:t>After</hp:t></hp:run></hp:p>")},
        ("section-0",),
    )

    # When: candidates are parsed and normalized.
    document = normalize_document(SourceFormat.HWPX, parse_hwpx(source))

    # Then: text and table blocks retain their source order.
    assert [(block.type, block.text) for block in document.blocks] == [
        ("paragraph", "Before"),
        ("table", "Metric\tValue"),
        ("paragraph", "After"),
    ]


def test_parse_hwpx_provides_rows_for_simple_table(tmp_path: Path) -> None:
    # Given: a rectangular HWPX table.
    body = """
    <hp:p><hp:run><hp:tbl>
      <hp:tr><hp:tc><hp:subList><hp:p><hp:run><hp:t>Item</hp:t></hp:run></hp:p></hp:subList></hp:tc><hp:tc><hp:subList><hp:p><hp:run><hp:t>Value</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr>
      <hp:tr><hp:tc><hp:subList><hp:p><hp:run><hp:t>Sales</hp:t></hp:run></hp:p></hp:subList></hp:tc><hp:tc><hp:subList><hp:p><hp:run><hp:t>123.4</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr>
    </hp:tbl></hp:run></hp:p>
    """
    source = _write_hwpx(
        tmp_path / "table.hwpx", {"section.xml": _section_xml(body)}, ("section-0",)
    )

    # When: the table is parsed.
    candidate = parse_hwpx(source)[1]

    # Then: its rows and serialized text preserve cell positions.
    assert isinstance(candidate, RawTable)
    assert candidate.rows == (("Item", "Value"), ("Sales", "123.4"))
    assert candidate.text == "Item\tValue\nSales\t123.4"


def test_parse_hwpx_leaves_blank_paragraph_for_normalization(tmp_path: Path) -> None:
    # Given: an empty paragraph before visible content.
    source = _write_hwpx(
        tmp_path / "blank.hwpx",
        {"section.xml": _section_xml("<hp:p/><hp:p><hp:run><hp:t>Content</hp:t></hp:run></hp:p>")},
        ("section-0",),
    )

    # When: parsed candidates are normalized.
    candidates = parse_hwpx(source)
    document = normalize_document(SourceFormat.HWPX, candidates)

    # Then: the raw blank survives parsing but not final blocks.
    assert isinstance(candidates[0], RawParagraph)
    assert candidates[0].text == ""
    assert [block.text for block in document.blocks] == ["Content"]


def test_parse_hwpx_assigns_only_recognized_style_roles(tmp_path: Path) -> None:
    # Given: paragraphs with exact Heading, Caption, and unknown styles.
    body = """
    <hp:p styleIDRef="h1"><hp:run><hp:t>Title</hp:t></hp:run></hp:p>
    <hp:p styleIDRef="caption"><hp:run><hp:t>Figure</hp:t></hp:run></hp:p>
    <hp:p styleIDRef="custom"><hp:run><hp:t>Body</hp:t></hp:run></hp:p>
    """
    source = _write_hwpx(
        tmp_path / "roles.hwpx", {"section.xml": _section_xml(body)}, ("section-0",)
    )

    # When: the document is parsed.
    candidates = parse_hwpx(source)

    # Then: only explicit, known styles receive non-body roles.
    assert [candidate.role for candidate in candidates] == [
        BlockRole.HEADING,
        BlockRole.CAPTION,
        BlockRole.BODY,
    ]


def test_parse_hwpx_marks_merged_table_partial(tmp_path: Path) -> None:
    # Given: a table cell spanning two columns.
    body = """
    <hp:p><hp:run><hp:tbl><hp:tr><hp:tc><hp:cellSpan colSpan="2" rowSpan="1"/><hp:subList><hp:p><hp:run><hp:t>Merged</hp:t></hp:run></hp:p></hp:subList></hp:tc></hp:tr></hp:tbl></hp:run></hp:p>
    """
    source = _write_hwpx(
        tmp_path / "merged.hwpx", {"section.xml": _section_xml(body)}, ("section-0",)
    )

    # When: the table is parsed and normalized.
    document = normalize_document(SourceFormat.HWPX, parse_hwpx(source))
    table = document.blocks[0]

    # Then: its text survives but no invented cell matrix is exposed.
    assert table.parse_status is ParseStatus.PARTIAL
    assert table.rows is None
    assert document.issues[0].code is ErrorCode.TABLE_ROWS_UNAVAILABLE


def test_parse_hwpx_records_unsupported_equation(tmp_path: Path) -> None:
    # Given: a paragraph with text and a math control.
    body = "<hp:p><hp:run><hp:t>Before</hp:t><hp:equation/><hp:t>After</hp:t></hp:run></hp:p>"
    source = _write_hwpx(
        tmp_path / "equation.hwpx", {"section.xml": _section_xml(body)}, ("section-0",)
    )

    # When: the HWPX is parsed and normalized.
    document = normalize_document(SourceFormat.HWPX, parse_hwpx(source))

    # Then: text fragments and the unsupported control remain distinguishable.
    assert [block.type for block in document.blocks] == ["paragraph", "unknown", "paragraph"]
    assert document.issues[0].code is ErrorCode.UNSUPPORTED_ELEMENT


def test_parse_hwpx_rejects_wrong_mimetype(tmp_path: Path) -> None:
    # Given: a ZIP package with an invalid HWPX mimetype marker.
    source = _write_hwpx(
        tmp_path / "wrong-mimetype.hwpx",
        {"section.xml": _section_xml("<hp:p/>")},
        ("section-0",),
        mimetype=b"application/not-hwpx",
    )

    # When: the package is parsed.
    with pytest.raises(HwpxParseError) as raised:
        parse_hwpx(source)

    # Then: it is identified as an invalid container.
    assert raised.value.code is ErrorCode.INVALID_CONTAINER


def test_parse_hwpx_rejects_damaged_zip_container(tmp_path: Path) -> None:
    # Given: a non-ZIP file carrying the HWPX extension.
    source = tmp_path / "damaged.hwpx"
    source.write_text("not a ZIP archive", encoding="utf-8")

    # When: the path is parsed as HWPX.
    with pytest.raises(HwpxParseError) as raised:
        parse_hwpx(source)

    # Then: the physical container failure is distinct from XML failures.
    assert raised.value.code is ErrorCode.INVALID_CONTAINER


def test_parse_hwpx_records_missing_spine_section(tmp_path: Path) -> None:
    # Given: a spine reference whose section file is absent from the archive.
    source = _write_hwpx(
        tmp_path / "missing-section.hwpx",
        {"section.xml": _section_xml("<hp:p/>")},
        ("section-0",),
        omitted_sections=frozenset({"section.xml"}),
    )

    # When: the package is parsed.
    candidates = parse_hwpx(source)

    # Then: the missing part is visible rather than silently skipped.
    assert candidates[0].code is ErrorCode.MISSING_REQUIRED_PART


def test_parse_hwpx_records_malformed_section_xml(tmp_path: Path) -> None:
    # Given: a spine section with malformed XML.
    source = _write_hwpx(
        tmp_path / "malformed-section.hwpx",
        {"section.xml": "<hs:sec>"},
        ("section-0",),
    )

    # When: the package is parsed.
    candidates = parse_hwpx(source)

    # Then: the malformed section is represented as an explicit failure.
    assert candidates[0].code is ErrorCode.MALFORMED_XML


def test_parse_hwpx_rejects_missing_required_header(tmp_path: Path) -> None:
    # Given: a package missing its required header XML.
    source = _write_hwpx(
        tmp_path / "missing-header.hwpx",
        {"section.xml": _section_xml("<hp:p/>")},
        ("section-0",),
        include_header=False,
    )

    # When: the package is parsed.
    with pytest.raises(HwpxParseError) as raised:
        parse_hwpx(source)

    # Then: the required XML failure has its own code.
    assert raised.value.code is ErrorCode.MISSING_REQUIRED_PART


def test_parse_hwpx_never_assigns_pages(tmp_path: Path) -> None:
    # Given: a normal HWPX document containing a paragraph.
    source = _write_hwpx(
        tmp_path / "pages.hwpx",
        {"section.xml": _section_xml("<hp:p><hp:run><hp:t>Text</hp:t></hp:run></hp:p>")},
        ("section-0",),
    )

    # When: candidates are parsed and normalized.
    candidates = parse_hwpx(source)
    document = normalize_document(SourceFormat.HWPX, candidates)

    # Then: neither layer invents a page reference.
    assert all(candidate.page is None for candidate in candidates)
    assert all(block.page is None for block in document.blocks)


def test_parse_hwpx_reads_main_sample_with_root_relative_spine_paths() -> None:
    # Given: an actual HWPX whose spine includes header.xml and Contents-prefixed hrefs.
    source = Path(__file__).resolve().parents[2] / "data/samples/sample-10-hwpx/report.hwpx"

    # When: the package is parsed through the common contract.
    document = normalize_document(SourceFormat.HWPX, parse_hwpx(source))
    text = "\n".join(block.text or "" for block in document.blocks)

    # Then: body blocks and source numeric expressions survive without invented pages.
    assert any(block.type == "paragraph" for block in document.blocks)
    assert any(block.type == "table" for block in document.blocks)
    assert all(block.page is None for block in document.blocks)
    assert all(value in text for value in ("1,488개", "26.5%", "97.78%"))
