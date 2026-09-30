from dataclasses import dataclass
from pathlib import Path
import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError
from pdfplumber.utils.exceptions import PdfminerException

from doc_parser.errors import ErrorCode
from doc_parser.models import PageRef, ParseStatus, serialize_rows
from doc_parser.normalize import RawBlock, RawParagraph, RawTable, RawUnknown


@dataclass(slots=True)
class PdfParseError(Exception):
    code: ErrorCode
    path: Path

    def __str__(self) -> str:
        return f"could not read PDF file {self.path}: {self.code.value}"


def parse_pdf(path: Path) -> tuple[RawBlock, ...]:
    try:
        with pdfplumber.open(path) as pdf:
            candidates: list[RawBlock] = []
            for page_number, page in enumerate(pdf.pages, start=1):
                candidates.extend(_page_candidates(page, PageRef(start=page_number, end=page_number)))
            return tuple(candidates)
    except PDFPasswordIncorrect as error:
        raise PdfParseError(ErrorCode.ENCRYPTED_DOCUMENT, path) from error
    except (OSError, PDFSyntaxError, PdfminerException) as error:
        raise PdfParseError(ErrorCode.INVALID_CONTAINER, path) from error


def _page_candidates(page: pdfplumber.page.Page, page_ref: PageRef) -> tuple[RawBlock, ...]:
    tables = tuple(
        group
        for group in _table_groups(page.find_tables())
        if _table_text(page, _group_bbox(group)) != ""
    )
    text = _page_text_without_tables(page, tuple(_group_bbox(group) for group in tables))
    candidates: list[RawBlock] = []
    if text != "":
        candidates.append(RawParagraph(text=text, page=page_ref))
    candidates.extend(_table_candidate(page, group, page_ref) for group in tables)
    if not candidates:
        candidates.append(
            RawUnknown(
                page=page_ref,
                code=ErrorCode.PDF_TEXT_UNAVAILABLE,
                message="PDF page contains no extractable text",
            )
        )
    return tuple(candidates)


def _table_candidate(
    page: pdfplumber.page.Page,
    tables: tuple[pdfplumber.table.Table, ...],
    page_ref: PageRef,
) -> RawTable:
    text = _table_text(page, _group_bbox(tables))
    rows = [row for table in tables for row in table.extract()]
    if _rows_are_simple(rows):
        normalized_rows = tuple(
            tuple("" if cell is None else cell for cell in row)
            for row in rows
        )
        return RawTable(
            text=serialize_rows([list(row) for row in normalized_rows]),
            rows=normalized_rows,
            page=page_ref,
        )
    return RawTable(
        text=text,
        rows=None,
        page=page_ref,
        parse_status=ParseStatus.PARTIAL,
    )


def _table_groups(
    tables: list[pdfplumber.table.Table],
) -> tuple[tuple[pdfplumber.table.Table, ...], ...]:
    groups: list[list[pdfplumber.table.Table]] = []
    for table in sorted(tables, key=lambda value: (value.bbox[1], value.bbox[0])):
        if groups and _continues_table(groups[-1][-1], table):
            groups[-1].append(table)
        else:
            groups.append([table])
    return tuple(tuple(group) for group in groups)


def _continues_table(
    previous: pdfplumber.table.Table, current: pdfplumber.table.Table
) -> bool:
    previous_x0, _, previous_x1, previous_bottom = previous.bbox
    current_x0, current_top, current_x1, _ = current.bbox
    return (
        abs(previous_x0 - current_x0) <= 2
        and abs(previous_x1 - current_x1) <= 2
        and 0 <= current_top - previous_bottom <= 24
    )


def _group_bbox(
    tables: tuple[pdfplumber.table.Table, ...],
) -> tuple[float, float, float, float]:
    x0, top, x1, bottom = tables[0].bbox
    for table in tables[1:]:
        table_x0, table_top, table_x1, table_bottom = table.bbox
        x0 = min(x0, table_x0)
        top = min(top, table_top)
        x1 = max(x1, table_x1)
        bottom = max(bottom, table_bottom)
    return x0, top, x1, bottom


def _rows_are_simple(rows: list[list[str | None]]) -> bool:
    if not rows or any(not row for row in rows):
        return False
    widths = {len(row) for row in rows}
    if len(widths) != 1:
        return False
    return all(cell is not None for row in rows for cell in row)


def _table_text(page: pdfplumber.page.Page, bbox: tuple[float, float, float, float]) -> str:
    return page.crop(bbox).extract_text() or ""


def _page_text_without_tables(
    page: pdfplumber.page.Page,
    table_boxes: tuple[tuple[float, float, float, float], ...],
) -> str:
    filtered = page.filter(
        lambda item: item["object_type"] != "char"
        or not _in_table_box(item, table_boxes)
    )
    return filtered.extract_text() or ""


def _in_table_box(
    item: dict[str, str | float],
    table_boxes: tuple[tuple[float, float, float, float], ...],
) -> bool:
    x_midpoint = (item["x0"] + item["x1"]) / 2
    y_midpoint = (item["top"] + item["bottom"]) / 2
    for x0, top, x1, bottom in table_boxes:
        if x0 <= x_midpoint <= x1 and top <= y_midpoint <= bottom:
            return True
    return False
