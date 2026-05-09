from __future__ import annotations

from bdd_agent.utils.gherkin_utils import FeatureDocument

GHERKIN_SYSTEM_PROMPT = """You are an expert BDD automation architect. Convert test cases into clean, business-readable Gherkin. Follow these rules:
- Each scenario must test one behavior only.
- Do not duplicate scenarios.
- Use Scenario Outline when same logic is repeated with different data.
- Create independent scenarios.
- Do not club multiple scenarios together.
- Include positive, negative, and edge cases.
- Use clear Given-When-Then format.
- Keep the language business-readable.
- Preserve test case traceability using tags.
- Avoid unnecessary technical details.
- Output only valid Gherkin."""



def build_gherkin_prompt(document: FeatureDocument, deterministic_output: str) -> str:
    return (
        f"Module: {document.module}\n"
        f"Feature: {document.feature}\n"
        "Polish the following draft Gherkin so it stays syntactically valid, keeps all tags and "
        "traceability information, and remains faithful to the original business behavior.\n\n"
        f"{deterministic_output}"
    )
