"""Conservatively label obvious non-verification numeric candidates.

This is intentionally a narrow, rule-only stage.  It never removes candidates
and it does not decide whether a remaining candidate is a research result.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


# A complete month/day expression takes priority over its individual year,
# month, and day tokens.
_DATE_RE = re.compile(r"(?:\d{4}\s*년\s*)?\d{1,2}\s*월\s*\d{1,2}\s*일")
_YEAR_RE = re.compile(r"\d{4}\s*(?:년|년도)")
_TABLE_RE = re.compile(r"<?\s*표\s*\d+(?:\s*-\s*\d+)*(?:\s*>)?")
_FIGURE_RE = re.compile(
    r"(?:\[\s*)?(?:그림|figure|fig\.)\s*\d+(?:\s*-\s*\d+)*(?:\s*\])?",
    re.IGNORECASE,
)
_SECTION_NAMED_RE = re.compile(r"제\s*\d+\s*(?:장|절|항|편)")
# Restrict outline numbering to the start of a line and require a following
# title-like word.  This avoids treating a prose decimal such as "값은 2.1" as
# a section number.
_SECTION_OUTLINE_RE = re.compile(
    r"^\s*\d+(?:\.\d+){1,3}(?=\s+[가-힣A-Za-z])", re.MULTILINE
)
_PAGE_RE = re.compile(
    r"(?:\bpp?\.\s*\d+(?:\s*-\s*\d+)?|\d+\s*쪽|페이지\s*\d+)",
    re.IGNORECASE,
)
# Do not match arbitrary bracketed text: every character inside must be a
# number, comma, hyphen, or whitespace.
_REFERENCE_RE = re.compile(r"\[\s*\d+(?:\s*(?:,|-)\s*\d+)*\s*\]")


def _overlaps(candidate_start: int, candidate_end: int, match: re.Match[str]) -> bool:
    return candidate_start < match.end() and candidate_end > match.start()


def _has_overlap(
    candidate_start: int, candidate_end: int, pattern: re.Pattern[str], context: str
) -> bool:
    return any(_overlaps(candidate_start, candidate_end, match) for match in pattern.finditer(context))


def _exclude_reason(candidate: Mapping[str, Any]) -> str | None:
    """Return an exclusion reason only for a clear structural marker."""

    context = candidate.get("context")
    start = candidate.get("start")
    end = candidate.get("end")
    if not isinstance(context, str) or not isinstance(start, int) or not isinstance(end, int):
        return None

    # Precedence matters: each token in a complete date is labelled ``date``.
    rules: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("date", _DATE_RE),
        ("table_number", _TABLE_RE),
        ("figure_number", _FIGURE_RE),
        ("section_number", _SECTION_NAMED_RE),
        ("section_number", _SECTION_OUTLINE_RE),
        ("page_number", _PAGE_RE),
        ("reference_number", _REFERENCE_RE),
        ("year", _YEAR_RE),
    )
    for reason, pattern in rules:
        if _has_overlap(start, end, pattern, context):
            return reason
    return None


def filter_obvious_non_verification_candidates(
    candidates: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Copy candidates and append conservative exclusion metadata.

    Input candidates are not modified, and every input candidate appears in the
    output in the same order.
    """

    filtered: list[dict[str, Any]] = []
    for candidate in candidates:
        result = dict(candidate)
        reason = _exclude_reason(candidate)
        result["exclude"] = reason is not None
        result["exclude_reason"] = reason
        filtered.append(result)
    return filtered
