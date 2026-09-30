from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from xml.etree.ElementTree import Element, ParseError
from zipfile import BadZipFile, ZipFile

from defusedxml import ElementTree as DefusedElementTree
from defusedxml.common import DefusedXmlException

from doc_parser.errors import ErrorCode
from doc_parser.models import BlockRole, ParseStatus, serialize_rows
from doc_parser.normalize import RawBlock, RawParagraph, RawTable, RawUnknown


MAX_ARCHIVE_MEMBERS = 2_048
MAX_MEMBER_BYTES = 25 * 1024 * 1024
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MIMETYPE = b"application/hwp+zip"
UNSUPPORTED_TAGS = frozenset({"equation", "ole", "picture", "shape", "video"})


@dataclass(slots=True)
class HwpxParseError(Exception):
    code: ErrorCode
    path: Path

    def __str__(self) -> str:
        return f"could not read HWPX file {self.path}: {self.code.value}"


def parse_hwpx(path: Path) -> tuple[RawBlock, ...]:
    with _open_archive(path) as archive:
        _validate_archive(archive, path)
        _validate_mimetype(archive, path)
        content_path = _content_path(archive, path)
        content_root = _read_xml(archive, content_path, path)
        header_root = _read_xml(
            archive, _relative_path(content_path, "header.xml", path), path
        )
        styles = _style_roles(header_root)
        candidates: list[RawBlock] = []
        for section_path in _spine_paths(
            archive,
            content_root,
            content_path,
            _relative_path(content_path, "header.xml", path),
            path,
        ):
            candidates.extend(_section_candidates(archive, section_path, path, styles))
        return tuple(candidates)


def _open_archive(path: Path) -> ZipFile:
    try:
        return ZipFile(path)
    except (BadZipFile, OSError) as error:
        raise HwpxParseError(ErrorCode.INVALID_CONTAINER, path) from error


def _validate_archive(archive: ZipFile, path: Path) -> None:
    entries = archive.infolist()
    if len(entries) > MAX_ARCHIVE_MEMBERS:
        raise HwpxParseError(ErrorCode.ARCHIVE_LIMITS_EXCEEDED, path)
    if any(info.flag_bits & 0x1 for info in entries):
        raise HwpxParseError(ErrorCode.ENCRYPTED_DOCUMENT, path)
    total_size = sum(info.file_size for info in entries)
    if total_size > MAX_ARCHIVE_BYTES or any(
        info.file_size > MAX_MEMBER_BYTES for info in entries
    ):
        raise HwpxParseError(ErrorCode.ARCHIVE_LIMITS_EXCEEDED, path)


def _validate_mimetype(archive: ZipFile, path: Path) -> None:
    try:
        mimetype = archive.read("mimetype")
    except KeyError as error:
        raise HwpxParseError(ErrorCode.MISSING_REQUIRED_PART, path) from error
    if mimetype != MIMETYPE:
        raise HwpxParseError(ErrorCode.INVALID_CONTAINER, path)


def _content_path(archive: ZipFile, path: Path) -> str:
    container_root = _read_xml(archive, "META-INF/container.xml", path)
    rootfile = next(
        (element for element in container_root.iter() if _name(element) == "rootfile"),
        None,
    )
    if rootfile is None:
        raise HwpxParseError(ErrorCode.INVALID_DOCUMENT_STRUCTURE, path)
    full_path = rootfile.get("full-path")
    if full_path is None:
        raise HwpxParseError(ErrorCode.INVALID_DOCUMENT_STRUCTURE, path)
    return _package_path(full_path, path)


def _spine_paths(
    archive: ZipFile,
    content_root: Element,
    content_path: str,
    header_path: str,
    path: Path,
) -> tuple[str, ...]:
    manifest = {
        item_id: href
        for element in content_root.iter()
        if _name(element) == "item"
        if (item_id := element.get("id")) is not None
        if (href := element.get("href")) is not None
    }
    spine = next(
        (element for element in content_root.iter() if _name(element) == "spine"),
        None,
    )
    if spine is None:
        raise HwpxParseError(ErrorCode.INVALID_DOCUMENT_STRUCTURE, path)
    paths: list[str] = []
    for itemref in spine:
        if _name(itemref) != "itemref":
            continue
        item_id = itemref.get("idref")
        if item_id is None or item_id not in manifest:
            raise HwpxParseError(ErrorCode.INVALID_DOCUMENT_STRUCTURE, path)
        manifest_path = _package_path(manifest[item_id], path)
        section_path = (
            manifest_path
            if manifest_path in archive.namelist()
            else _relative_path(content_path, manifest_path, path)
        )
        if section_path != header_path:
            paths.append(section_path)
    if not paths:
        raise HwpxParseError(ErrorCode.INVALID_DOCUMENT_STRUCTURE, path)
    return tuple(paths)


def _section_candidates(
    archive: ZipFile,
    section_path: str,
    path: Path,
    styles: dict[str, BlockRole],
) -> tuple[RawBlock, ...]:
    try:
        section_root = _read_xml(archive, section_path, path)
    except HwpxParseError as error:
        return (_unknown(error.code, f"could not parse section {section_path}"),)
    if _name(section_root) != "sec":
        return ()
    candidates: list[RawBlock] = []
    for element in section_root:
        if _name(element) == "p":
            candidates.extend(_paragraph_candidates(element, styles))
        else:
            candidates.append(_unknown(ErrorCode.UNSUPPORTED_ELEMENT, "unsupported section element"))
    return tuple(candidates)


def _paragraph_candidates(
    paragraph: Element, styles: dict[str, BlockRole]
) -> tuple[RawBlock, ...]:
    candidates: list[RawBlock] = []
    text_parts: list[str] = []

    def flush_text() -> None:
        candidates.append(
            RawParagraph(
                text="".join(text_parts),
                role=styles.get(paragraph.get("styleIDRef", ""), BlockRole.BODY),
            )
        )
        text_parts.clear()

    def visit(element: Element) -> None:
        tag_name = _name(element)
        if tag_name == "tbl":
            flush_text()
            candidates.extend(_table_candidates(element))
            return
        if tag_name in UNSUPPORTED_TAGS:
            flush_text()
            candidates.append(
                _unknown(ErrorCode.UNSUPPORTED_ELEMENT, f"unsupported HWPX {tag_name}")
            )
            return
        if tag_name == "t":
            text_parts.append(element.text or "")
            return
        if tag_name == "lineBreak":
            text_parts.append("\n")
            return
        if tag_name == "tab":
            text_parts.append("\t")
            return
        for child in element:
            visit(child)

    for child in paragraph:
        visit(child)
    flush_text()
    return tuple(candidates)


def _table_candidates(table: Element) -> tuple[RawBlock, ...]:
    rows = tuple(
        tuple(_cell_text(cell) for cell in row if _name(cell) == "tc")
        for row in table
        if _name(row) == "tr"
    )
    text = serialize_rows([list(row) for row in rows])
    complex_table = _table_is_complex(table, rows)
    result: list[RawBlock] = [
        RawTable(
            text=text,
            rows=None if complex_table else rows,
            parse_status=ParseStatus.PARTIAL if complex_table else ParseStatus.COMPLETE,
        )
    ]
    result.extend(_unsupported_table_candidates(table))
    return tuple(result)


def _table_is_complex(table: Element, rows: tuple[tuple[str, ...], ...]) -> bool:
    widths = {len(row) for row in rows}
    if len(widths) > 1:
        return True
    for element in table.iter():
        if _name(element) == "tbl" and element is not table:
            return True
        if _name(element) == "tc" and (
            element.get("colSpan", "1") != "1" or element.get("rowSpan", "1") != "1"
        ):
            return True
        if _name(element) == "cellSpan" and (
            element.get("colSpan", "1") != "1" or element.get("rowSpan", "1") != "1"
        ):
            return True
    return False


def _cell_text(cell: Element) -> str:
    paragraphs = [element for element in cell.iter() if _name(element) == "p"]
    return "\n".join(_paragraph_text(paragraph) for paragraph in paragraphs)


def _paragraph_text(paragraph: Element) -> str:
    parts: list[str] = []
    for element in paragraph.iter():
        tag_name = _name(element)
        if tag_name == "t":
            parts.append(element.text or "")
        elif tag_name == "lineBreak":
            parts.append("\n")
        elif tag_name == "tab":
            parts.append("\t")
    return "".join(parts)


def _unsupported_table_candidates(table: Element) -> tuple[RawUnknown, ...]:
    return tuple(
        _unknown(ErrorCode.UNSUPPORTED_ELEMENT, f"unsupported HWPX {tag_name}")
        for element in table.iter()
        if (tag_name := _name(element)) in UNSUPPORTED_TAGS
    )


def _style_roles(header_root: Element) -> dict[str, BlockRole]:
    roles: dict[str, BlockRole] = {}
    for element in header_root.iter():
        if _name(element) != "style":
            continue
        style_id = element.get("id")
        style_name = element.get("name")
        if style_id is None or style_name is None:
            continue
        if style_name.startswith("Heading "):
            roles[style_id] = BlockRole.HEADING
        elif style_name == "Caption":
            roles[style_id] = BlockRole.CAPTION
    return roles


def _read_xml(archive: ZipFile, member: str, path: Path) -> Element:
    try:
        payload = archive.read(member)
    except KeyError as error:
        raise HwpxParseError(ErrorCode.MISSING_REQUIRED_PART, path) from error
    try:
        return DefusedElementTree.fromstring(payload)
    except (DefusedXmlException, ParseError) as error:
        raise HwpxParseError(ErrorCode.MALFORMED_XML, path) from error


def _relative_path(base: str, relative: str, path: Path) -> str:
    return _package_path(str(PurePosixPath(base).parent / relative), path)


def _package_path(value: str, path: Path) -> str:
    package_path = PurePosixPath(value)
    if package_path.is_absolute() or ".." in package_path.parts:
        raise HwpxParseError(ErrorCode.INVALID_DOCUMENT_STRUCTURE, path)
    return str(package_path)


def _name(element: Element) -> str:
    return element.tag.rsplit("}", maxsplit=1)[-1]


def _unknown(code: ErrorCode, message: str) -> RawUnknown:
    return RawUnknown(page=None, code=code, message=message)
