"""Extract numeric candidates from parser-normalized document nodes.

This module deliberately performs no semantic filtering.  Dates, section
numbers, table numbers, and any other numeric-looking text are candidates at
this stage; a later pipeline stage decides what is worth verification.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


# A comma-separated integer must be matched before a plain integer so that
# ``1,248`` is emitted as one candidate rather than two.
_NUMBER = r"[-+]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"

# Keep this intentionally conservative.  Unknown adjacent text does not stop
# extraction: it is returned as a number without a unit instead of being lost.
_UNIT = r"(?:%|(?:조|억|만|천)\s*원|조원|억원|만원|천원|시간|분|초|년|월|일|명|건|개|회|곳|쪽|배|점|원|km|cm|mm|kg|mg|g|ml|mL|L|MB|GB|TB|Hz|kHz|MHz|GHz|℃|°C|도)"
_RANGE_SEPARATOR = r"(?:~|–|-)"
_SUPERSCRIPT_EXPONENT = r"[⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+"

_CANDIDATE_RE = re.compile(
    rf"""
    (?<![0-9A-Za-z_])
    (?:
        # Keep a confidence level separate from the bounds it qualifies.
        (?P<confidence_interval>
            (?P<confidence_level>\d+(?:\.\d+)?)\s*%\s*CI(?:\s*(?:는|은))?\s*(?::|=)?\s*
            (?:
                \[\s*(?P<ci_bracket_start>{_NUMBER})\s*,\s*(?P<ci_bracket_end>{_NUMBER})\s*\]
              |
                (?P<ci_range_start>{_NUMBER})\s*{_RANGE_SEPARATOR}\s*(?P<ci_range_end>{_NUMBER})
            )
            (?:\s*(?P<ci_unit>{_UNIT}))?
        )
      |
        # Preserve the p statistic and its inequality operator.
        (?P<inequality>
            (?P<inequality_statistic>[pP])\s*
            (?P<inequality_operator><=|>=|<|>|≤|≥)\s*
            (?P<inequality_number>{_NUMBER})(?:\s*(?P<inequality_unit>{_UNIT}))?
        )
      |
        # Preserve a p-value assignment as one raw expression.
        (?P<pvalue>[pP]\s*=\s*(?P<pvalue_number>{_NUMBER})(?:\s*(?P<pvalue_unit>{_UNIT}))?)
      |
        # The central estimate is value; preserve its uncertainty separately.
        (?P<plusminus>
            (?P<plusminus_number>{_NUMBER})\s*±\s*(?P<plusminus_error>{_NUMBER})
            (?:\s*(?P<plusminus_unit>{_UNIT}))?
        )
      |
        # Normalize ASCII and Unicode-superscript scientific notation.
        (?P<scientific_multiplication>
            (?P<scientific_mantissa>{_NUMBER})\s*[×xX]\s*10\s*
            (?:\^\s*(?P<scientific_ascii_exponent>[-+]?\d+)|(?P<scientific_superscript_exponent>{_SUPERSCRIPT_EXPONENT}))
            (?:\s*(?P<scientific_unit>{_UNIT}))?
        )
      |
        (?P<scientific_power>
            10(?P<power_superscript_exponent>{_SUPERSCRIPT_EXPONENT})(?:\s*(?P<power_unit>{_UNIT}))?
        )
      |
        # A range is one candidate even when each endpoint carries a unit.
        (?P<range>
            (?<!\[)(?P<range_start>{_NUMBER})(?:\s*(?P<range_start_unit>{_UNIT}))?\s*
            {_RANGE_SEPARATOR}\s*
            (?P<range_end>{_NUMBER})(?:\s*(?P<range_end_unit>{_UNIT}))?(?!\s*>)
        )
      |
        (?P<basic>(?P<basic_number>{_NUMBER})(?:\s*(?P<basic_unit>{_UNIT}))?)
    )
    # A comma followed by whitespace starts a separate list item (``[3, 5]``),
    # while a comma immediately followed by digits remains part of a number.
    (?![0-9.]|,(?!\s))
    """,
    re.VERBOSE,
)


def _to_float(number_text: str) -> float:
    """Convert a document number to a comparison-friendly float."""

    return float(number_text.replace(",", ""))


def _superscript_to_int(exponent_text: str) -> int:
    """Convert a Unicode superscript exponent such as ``⁻³`` to an integer."""

    translation = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
    return int(exponent_text.translate(translation))


def extract_numeric_candidates(node: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return every numeric-looking candidate found in one common document node.

    Required parser fields are normally ``text``, ``page``, ``type``, and
    ``order``.  Missing metadata is passed through as ``None`` so a malformed
    node cannot stop extraction of other nodes.
    """

    text = node.get("text")
    if not isinstance(text, str) or not text:
        return []

    candidates: list[dict[str, Any]] = []
    for match in _CANDIDATE_RE.finditer(text):
        extra: dict[str, Any] = {}
        if match.group("confidence_interval") is not None:
            raw = match.group("confidence_interval")
            start_text = match.group("ci_bracket_start") or match.group("ci_range_start")
            end_text = match.group("ci_bracket_end") or match.group("ci_range_end")
            value = _to_float(start_text)
            unit = match.group("ci_unit") or ""
            extra = {
                "confidence_level": _to_float(match.group("confidence_level")),
                "range_start": value,
                "range_end": _to_float(end_text),
            }
        elif match.group("inequality") is not None:
            raw = match.group("inequality")
            value = _to_float(match.group("inequality_number"))
            unit = match.group("inequality_unit") or ""
            extra = {
                "operator": match.group("inequality_operator"),
                "statistic": match.group("inequality_statistic").lower(),
            }
        elif match.group("pvalue") is not None:
            raw = match.group("pvalue")
            value = _to_float(match.group("pvalue_number"))
            unit = match.group("pvalue_unit") or ""
        elif match.group("plusminus") is not None:
            raw = match.group("plusminus")
            value = _to_float(match.group("plusminus_number"))
            unit = match.group("plusminus_unit") or ""
            extra = {"error": _to_float(match.group("plusminus_error"))}
        elif match.group("scientific_multiplication") is not None:
            raw = match.group("scientific_multiplication")
            exponent_text = match.group("scientific_ascii_exponent")
            exponent = (
                int(exponent_text)
                if exponent_text is not None
                else _superscript_to_int(match.group("scientific_superscript_exponent"))
            )
            value = _to_float(match.group("scientific_mantissa")) * (
                10**exponent
            )
            unit = match.group("scientific_unit") or ""
        elif match.group("scientific_power") is not None:
            raw = match.group("scientific_power")
            value = 10 ** _superscript_to_int(match.group("power_superscript_exponent"))
            unit = match.group("power_unit") or ""
        elif match.group("range") is not None:
            raw = match.group("range")
            value = _to_float(match.group("range_start"))
            unit = match.group("range_end_unit") or match.group("range_start_unit") or ""
            extra = {"range_end": _to_float(match.group("range_end"))}
        else:
            raw = match.group("basic")
            value = _to_float(match.group("basic_number"))
            unit = match.group("basic_unit") or ""

        candidate = {
            "raw": raw,
            "value": value,
            "unit": unit,
            "context": text,
            "page": node.get("page"),
            "type": node.get("type"),
            "order": node.get("order"),
            "start": match.start(),
            "end": match.end(),
        }
        candidate.update(extra)
        candidates.append(candidate)

    return candidates
