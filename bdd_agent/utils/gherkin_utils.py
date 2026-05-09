from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class ScenarioExample:
    values: dict[str, str]


@dataclass
class ScenarioDocument:
    title: str
    tags: list[str]
    traceability_ids: list[str]
    steps: list[str]
    scenario_type: str
    examples: list[ScenarioExample] = field(default_factory=list)
    case_type: str = "positive"


@dataclass
class FeatureDocument:
    module: str
    feature: str
    tags: list[str]
    scenarios: list[ScenarioDocument] = field(default_factory=list)
    background_steps: list[str] = field(default_factory=list)
    content: str = ""



def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return cleaned.strip("_") or "general"



def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return cleaned.strip("_") or "feature"



def build_feature_key(module: str, feature: str) -> str:
    return f"{slugify(module)}::{slugify(feature)}"



def build_tags(case: dict, feature_level: bool) -> list[str]:
    tags = {f"@module_{slugify(case.get('module', 'general'))}", f"@feature_{slugify(case.get('feature', 'general'))}"}
    if not feature_level:
        tags.add(f"@{slugify(case.get('case_type', 'positive'))}")
        tags.add("@regression")
        priority = case.get("priority", "").strip().lower()
        if priority in {"high", "critical", "p1", "p0"}:
            tags.add("@smoke")
        if case.get("test_case_id"):
            tags.add(f"@tc_{slugify(case['test_case_id'])}")
    return sorted(tags)



def build_scenario_steps(case: dict) -> list[str]:
    steps: list[str] = []

    preconditions = case.get("preconditions", [])
    if preconditions:
        first, *rest = preconditions
        steps.append(f"Given {first}")
        steps.extend(f"And {step}" for step in rest)
    else:
        steps.append(f"Given the user is working with {case.get('feature', 'the feature')}")

    action_steps = case.get("steps", [])
    if action_steps:
        first, *rest = action_steps
        steps.append(f"When {first}")
        steps.extend(f"And {step}" for step in rest)
    else:
        steps.append("When the user performs the business action")

    expected_result = case.get("expected_result", "") or "the expected outcome should be achieved"
    steps.append(f"Then {expected_result}")
    return steps



def build_examples(cases: list[dict]) -> list[ScenarioExample]:
    parsed_keys: list[str] = []
    for case in cases:
        for key in case.get("test_data", {}).keys():
            if key not in parsed_keys:
                parsed_keys.append(key)
    if parsed_keys:
        return [ScenarioExample({key: case.get("test_data", {}).get(key, "") for key in parsed_keys}) for case in cases]
    raw_values = [case.get("test_data_raw", "") for case in cases if case.get("test_data_raw")]
    if raw_values:
        return [ScenarioExample({"test_data": case.get("test_data_raw", "")}) for case in cases]
    return []



def placeholderize_scenario(steps: list[str], values: dict[str, str]) -> list[str]:
    replaced_steps = steps[:]
    for key, value in values.items():
        if not value:
            continue
        placeholder = f"<{slugify(key)}>"
        replaced_steps = [step.replace(value, placeholder) for step in replaced_steps]
    if replaced_steps == steps:
        keys = [slugify(key) for key in values]
        if not keys:
            keys = ["test_data"]
        placeholders = [f"<{key}>" for key in keys]
        if len(placeholders) == 1:
            data_step = f"And the input data {placeholders[0]} is provided"
        else:
            data_step = f"And the input data includes {' and '.join(placeholders)}"
        replaced_steps.insert(-1, data_step)
    return replaced_steps



def build_background_steps(scenarios: Iterable[ScenarioDocument]) -> list[str]:
    first_steps = [scenario.steps[0] for scenario in scenarios if scenario.steps and scenario.steps[0].startswith("Given ")]
    if not first_steps:
        return []
    counts = Counter(first_steps)
    most_common_step, count = counts.most_common(1)[0]
    if count < 2:
        return []
    for scenario in scenarios:
        if scenario.steps and scenario.steps[0] == most_common_step:
            scenario.steps = scenario.steps[1:]
    return [most_common_step]



def ensure_unique_title(title: str, used_titles: set[str]) -> str:
    base_title = title.strip() or "Unnamed scenario"
    candidate = base_title
    counter = 2
    while candidate.lower() in used_titles:
        candidate = f"{base_title} ({counter})"
        counter += 1
    used_titles.add(candidate.lower())
    return candidate



def render_feature_document(document: FeatureDocument) -> str:
    lines: list[str] = []
    if document.tags:
        lines.append(" ".join(document.tags))
    lines.append(f"Feature: {document.feature}")
    lines.append(f"  Business coverage for the {document.module} module.")
    lines.append("")

    if document.background_steps:
        lines.append("  Background:")
        for step in document.background_steps:
            lines.append(f"    {step}")
        lines.append("")

    for scenario in document.scenarios:
        if scenario.tags:
            lines.append(f"  {' '.join(scenario.tags)}")
        lines.append(f"  {scenario.scenario_type}: {scenario.title}")
        for traceability_id in scenario.traceability_ids:
            lines.append(f"    # Traceability: {traceability_id}")
        for step in scenario.steps:
            lines.append(f"    {step}")
        if scenario.scenario_type == "Scenario Outline":
            example_headers = list(scenario.examples[0].values.keys()) if scenario.examples else []
            lines.append("    Examples:")
            lines.append(f"      | {' | '.join(example_headers)} |")
            for example in scenario.examples:
                lines.append(
                    f"      | {' | '.join(example.values.get(header, '') for header in example_headers)} |"
                )
        lines.append("")

    return "\n".join(lines).strip() + "\n"



def validate_feature_document(document: FeatureDocument) -> list[str]:
    errors: list[str] = []
    seen_titles: set[str] = set()
    seen_flows: set[tuple[str, ...]] = set()

    for scenario in document.scenarios:
        title_key = scenario.title.lower()
        if title_key in seen_titles:
            errors.append(f"Duplicate scenario title in feature '{document.feature}': {scenario.title}")
        seen_titles.add(title_key)

        flow_key = tuple(step.lower() for step in scenario.steps)
        if flow_key in seen_flows:
            errors.append(f"Duplicate scenario flow in feature '{document.feature}': {scenario.title}")
        seen_flows.add(flow_key)

        if not document.background_steps and not any(step.startswith("Given") for step in scenario.steps):
            errors.append(f"Scenario missing Given step: {scenario.title}")
        if not any(step.startswith("When") for step in scenario.steps):
            errors.append(f"Scenario missing When step: {scenario.title}")
        if not any(step.startswith("Then") for step in scenario.steps):
            errors.append(f"Scenario missing Then step: {scenario.title}")
        if scenario.scenario_type == "Scenario Outline" and not scenario.examples:
            errors.append(f"Scenario Outline missing Examples: {scenario.title}")

    return errors
