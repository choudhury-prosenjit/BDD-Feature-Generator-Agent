from __future__ import annotations

import re
from typing import Any



def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())



def classify_case_type(case: dict[str, Any]) -> str:
    explicit_type = _normalize(case.get("case_type", ""))
    if explicit_type in {"positive", "negative", "edge"}:
        return explicit_type

    searchable = " ".join(
        [
            case.get("title", ""),
            " ".join(case.get("steps", [])),
            case.get("expected_result", ""),
        ]
    ).lower()
    if any(keyword in searchable for keyword in ["invalid", "error", "fail", "reject", "negative"]):
        return "negative"
    if any(keyword in searchable for keyword in ["boundary", "limit", "edge", "empty", "maximum", "minimum"]):
        return "edge"
    return "positive"



def build_duplicate_key(case: dict[str, Any]) -> tuple:
    return (
        _normalize(case.get("module", "")),
        _normalize(case.get("feature", "")),
        _normalize(case.get("title", "")),
        tuple(_normalize(step) for step in case.get("preconditions", [])),
        tuple(_normalize(step) for step in case.get("steps", [])),
        tuple(
            sorted(
                (_normalize(key), _normalize(value))
                for key, value in case.get("test_data", {}).items()
            )
        ),
        _normalize(case.get("test_data_raw", "")),
        _normalize(case.get("expected_result", "")),
    )



def build_behavior_key(case: dict[str, Any]) -> tuple:
    return (
        _normalize(case.get("module", "")),
        _normalize(case.get("feature", "")),
        _normalize(case.get("title", "")),
        tuple(_normalize(step) for step in case.get("preconditions", [])),
        tuple(_normalize(step) for step in case.get("steps", [])),
        _normalize(case.get("expected_result", "")),
        case.get("case_type", "positive"),
    )
