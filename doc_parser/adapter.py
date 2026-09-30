from typing import assert_never

from doc_parser.models import BlockRole, Document, ParagraphBlock, TableBlock, UnknownBlock


# Confirm the caption type with the numeric-collection owner before integration.
def to_collector_blocks(document: Document) -> list[dict]:
    result: list[dict] = []
    for block in document.blocks:
        match block:
            case ParagraphBlock(text=None):
                continue
            case ParagraphBlock(
                text=text, page=page, order=order, role=BlockRole.CAPTION
            ):
                result.append(
                    {
                        "type": "caption",
                        "text": text,
                        "page": None if page is None else page.start,
                        "order": order,
                    }
                )
            case ParagraphBlock(text=text, page=page, order=order):
                result.append(
                    {
                        "type": "paragraph",
                        "text": text,
                        "page": None if page is None else page.start,
                        "order": order,
                    }
                )
            case TableBlock(text=None):
                continue
            case TableBlock(text=text, page=page, order=order, rows=rows):
                result.append(
                    {
                        "type": "table",
                        "text": text,
                        "page": None if page is None else page.start,
                        "order": order,
                        "rows": rows,
                    }
                )
            case UnknownBlock():
                continue
            case unreachable:
                assert_never(unreachable)
    return result
