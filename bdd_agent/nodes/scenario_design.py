from __future__ import annotations

from collections import defaultdict

from bdd_agent.utils.duplicate_checker import build_behavior_key, build_duplicate_key
from bdd_agent.utils.gherkin_utils import (
    FeatureDocument,
    ScenarioDocument,
    ScenarioExample,
    build_background_steps,
    build_examples,
    build_feature_key,
    build_scenario_steps,
    build_tags,
    ensure_unique_title,
    placeholderize_scenario,
)



def scenario_design_node(state: dict) -> dict:
    feature_documents: dict[str, FeatureDocument] = {}
    grouped_cases: dict[tuple, list[dict]] = defaultdict(list)
    seen_duplicate_keys: set[tuple] = set()

    for case in state.get("classified_test_cases", []):
        duplicate_key = build_duplicate_key(case)
        if case.get("is_duplicate_candidate") and duplicate_key in seen_duplicate_keys:
            continue
        seen_duplicate_keys.add(duplicate_key)
        grouped_cases[build_behavior_key(case)].append(case)

    used_titles: dict[str, set[str]] = defaultdict(set)

    for group_cases in grouped_cases.values():
        sample = group_cases[0]
        feature_key = build_feature_key(sample["module"], sample["feature"])
        document = feature_documents.setdefault(
            feature_key,
            FeatureDocument(
                module=sample["module"],
                feature=sample["feature"],
                tags=build_tags(sample, feature_level=True),
                scenarios=[],
            ),
        )

        outline_examples = build_examples(group_cases)
        scenario_steps = build_scenario_steps(sample)
        outline = len(group_cases) > 1 and len(outline_examples) > 1

        if outline:
            scenario_steps = placeholderize_scenario(scenario_steps, outline_examples[0].values)

        scenario = ScenarioDocument(
            title=ensure_unique_title(sample["title"], used_titles[feature_key]),
            tags=build_tags(sample, feature_level=False),
            traceability_ids=[case["test_case_id"] for case in group_cases if case.get("test_case_id")],
            steps=scenario_steps,
            scenario_type="Scenario Outline" if outline else "Scenario",
            examples=outline_examples if outline else [],
            case_type=sample["case_type"],
        )
        document.scenarios.append(scenario)

    for document in feature_documents.values():
        document.background_steps = build_background_steps(document.scenarios)

    return {"feature_documents": feature_documents}
