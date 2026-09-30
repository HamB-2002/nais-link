"""Classify numeric candidates for provenance tracing without changing values.

The default path is deliberately conservative and rule-based.  A caller may
inject an LLM-backed classifier later, but this module has no provider SDK,
network call, or credential handling.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from typing import Any


VerificationStatus = str
Classifier = Callable[[dict[str, Any]], object]
_VALID_STATUSES = frozenset({"VERIFY", "IGNORE", "UNCERTAIN"})

_IGNORE_PATTERNS = (
    (re.compile(r"연구\s*기간|조사\s*기간"), "study or survey duration"),
    (re.compile(r"연구비|사업비|예산"), "research budget or project cost"),
    (re.compile(r"\bversion\b|버전"), "software or data version"),
    (re.compile(r"\bpython\b|\bstata\b|\bsas\b|\bmatlab\b|\br\s+version\b"), "software version or environment"),
)
_VERIFY_PATTERNS = (
    re.compile(r"표본|관측|응답|분석\s*(?:했|한|결과|대상)|분석하였다"),
    re.compile(r"평균|중앙값|비율|백분율|증가율|감소율|증감률|정확도"),
    re.compile(r"precision|recall|\bf1\b|손실(?:값)?|\bloss\b", re.IGNORECASE),
    re.compile(r"회귀|상관|계수|표준편차|표준오차|신뢰구간|검정|통계량"),
    re.compile(r"\br[²2]\b|집계|분석 결과|조사 결과", re.IGNORECASE),
)
_CONFIGURATION_PATTERN = re.compile(r"임계값|threshold|설정", re.IGNORECASE)


def _rule_decision(candidate: Mapping[str, Any]) -> tuple[VerificationStatus, str]:
    """Return only decisive rule outcomes; otherwise retain uncertainty."""

    if candidate.get("exclude") is True:
        reason = candidate.get("exclude_reason") or "non-verification filter"
        return "IGNORE", f"excluded by non-verification filter: {reason}"

    context = candidate.get("context")
    if not isinstance(context, str):
        return "UNCERTAIN", "missing textual context"

    normalized_context = context.lower()
    for pattern, reason in _IGNORE_PATTERNS:
        if pattern.search(normalized_context):
            return "IGNORE", f"rule: {reason}"

    if candidate.get("statistic") == "p":
        return "VERIFY", "rule: p-value or p-value inequality"
    if "confidence_level" in candidate:
        return "VERIFY", "rule: confidence interval"
    if "error" in candidate:
        return "VERIFY", "rule: estimate with reported uncertainty"
    if any(pattern.search(context) for pattern in _VERIFY_PATTERNS):
        return "VERIFY", "rule: analysis-result language in context"
    if _CONFIGURATION_PATTERN.search(normalized_context):
        return "UNCERTAIN", "rule: configuration value may be an input rather than a result"

    return "UNCERTAIN", "rule: insufficient context to determine provenance value"


def _minimal_classifier_payload(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return the only document fields an external classifier may receive."""

    return {
        "raw": candidate.get("raw"),
        "unit": candidate.get("unit"),
        "context": candidate.get("context"),
        "type": candidate.get("type"),
    }


def _validated_classifier_response(response: object) -> tuple[VerificationStatus, str] | None:
    """Validate injected-classifier output before trusting it."""

    if isinstance(response, str):
        status = response.strip()
        reason = "classifier returned a valid status"
    elif isinstance(response, Mapping):
        status = response.get("status")
        reason = response.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            reason = "classifier returned a valid status"
    else:
        return None

    if status not in _VALID_STATUSES:
        return None
    return status, reason


def classify_candidate(
    candidate: Mapping[str, Any], classifier: Classifier | None = None
) -> dict[str, Any]:
    """Copy one candidate and append verification classification metadata.

    Excluded candidates never reach the injected classifier.  A classifier is
    called only for rule-level ``UNCERTAIN`` cases, and invalid or failed output
    safely remains ``UNCERTAIN``.
    """

    result = dict(candidate)
    status, reason = _rule_decision(candidate)

    if status != "UNCERTAIN" or classifier is None:
        result.update(
            {
                "verification_status": status,
                "verification_reason": reason,
                "verification_method": "rule",
            }
        )
        return result

    try:
        response = classifier(_minimal_classifier_payload(candidate))
    except Exception:
        result.update(
            {
                "verification_status": "UNCERTAIN",
                "verification_reason": "classifier failed; retained as uncertain",
                "verification_method": "rule",
            }
        )
        return result

    validated = _validated_classifier_response(response)
    if validated is None:
        result.update(
            {
                "verification_status": "UNCERTAIN",
                "verification_reason": "invalid classifier response; retained as uncertain",
                "verification_method": "rule",
            }
        )
        return result

    llm_status, llm_reason = validated
    result.update(
        {
            "verification_status": llm_status,
            "verification_reason": llm_reason,
            "verification_method": "llm",
        }
    )
    return result


def classify_candidates(
    candidates: Iterable[Mapping[str, Any]], classifier: Classifier | None = None
) -> list[dict[str, Any]]:
    """Classify candidates in order without deleting or mutating input items."""

    return [classify_candidate(candidate, classifier=classifier) for candidate in candidates]
