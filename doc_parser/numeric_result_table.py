"""Format classified numeric candidates for downstream consumers and review UIs.

The structured ``list[dict]`` returned here is the canonical formatter output.
Markdown rendering is provided only as a human-review convenience.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


_VALID_STATUSES = frozenset({"VERIFY", "IGNORE", "UNCERTAIN"})
_MARKDOWN_COLUMNS = (
    "display_location",
    "raw",
    "value",
    "unit",
    "context",
    "verification_status",
    "verification_method",
)


def _display_order(order: object) -> str:
    """Render an optional source order without requiring a valid integer."""

    return "?" if order is None else str(order)


def _page_prefix(page: object) -> str:
    """Render only actual integer page references as a display prefix."""

    return f"p.{page} · " if isinstance(page, int) and not isinstance(page, bool) else ""


def _display_location(result: Mapping[str, Any]) -> str:
    """Build a human-readable location without changing source coordinates."""

    page_prefix = _page_prefix(result.get("page"))
    order = _display_order(result.get("order"))
    block_type = result.get("type")

    if block_type == "paragraph":
        return f"{page_prefix}문단 #{order}"
    if block_type == "caption":
        return f"{page_prefix}캡션 #{order}"
    if block_type == "table":
        row = result.get("row")
        column = result.get("column")
        if (
            isinstance(row, int)
            and not isinstance(row, bool)
            and isinstance(column, int)
            and not isinstance(column, bool)
        ):
            return f"{page_prefix}표 block #{order} · {row + 1}행 {column + 1}열"
        return f"{page_prefix}표 block #{order}"
    return f"{page_prefix}block #{order}"


def format_numeric_results(candidates: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Copy classified candidates into stable, JSON-serializable result rows.

    Existing fields, including compound-number details and future extensions,
    remain at the top level.  ``row`` and ``column`` are stabilized to ``None``
    when a candidate has no table-cell coordinates.
    """

    results: list[dict[str, Any]] = []
    for candidate in candidates:
        result = dict(candidate)
        result.setdefault("row", None)
        result.setdefault("column", None)
        result["display_location"] = _display_location(result)
        results.append(result)
    return results


def select_results_by_status(
    results: Iterable[Mapping[str, Any]], status: str
) -> list[dict[str, Any]]:
    """Return copied result rows with one explicitly allowed verification status."""

    if status not in _VALID_STATUSES:
        raise ValueError(f"unsupported verification status: {status!r}")
    return [dict(result) for result in results if result.get("verification_status") == status]


def select_verify_results(results: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return copied rows whose verification status is ``VERIFY``."""

    return select_results_by_status(results, "VERIFY")


def _markdown_cell(value: object) -> str:
    """Escape one value for a Markdown table cell."""

    if value is None:
        return "—"
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\r\n", "<br>").replace("\r", "<br>").replace("\n", "<br>")


def to_markdown_table(results: Iterable[Mapping[str, Any]]) -> str:
    """Render result rows as a Markdown review table without changing them."""

    header = "| " + " | ".join(_MARKDOWN_COLUMNS) + " |"
    separator = "| " + " | ".join("---" for _ in _MARKDOWN_COLUMNS) + " |"
    body = [
        "| " + " | ".join(_markdown_cell(result.get(column)) for column in _MARKDOWN_COLUMNS) + " |"
        for result in results
    ]
    return "\n".join([header, separator, *body])
