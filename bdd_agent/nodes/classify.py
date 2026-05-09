from __future__ import annotations

from collections import Counter

from bdd_agent.utils.duplicate_checker import build_duplicate_key, classify_case_type



def classify_test_cases_node(state: dict) -> dict:
    cases = []
    duplicate_counter = Counter(build_duplicate_key(case) for case in state.get("normalized_test_cases", []))

    for case in state.get("normalized_test_cases", []):
        enriched = dict(case)
        enriched["case_type"] = classify_case_type(case)
        enriched["is_duplicate_candidate"] = duplicate_counter[build_duplicate_key(case)] > 1
        cases.append(enriched)

    return {"classified_test_cases": cases}
