"""
bdd_generator.py
----------------
Core logic for converting Excel test-case data into BDD feature files.

Flow
----
1. load_excel(file)          – read the Excel workbook into a DataFrame
2. parse_test_cases(df)      – normalise column names and build a list of
                               structured test-case dicts
3. load_guidelines()         – read guidelines.md from the project root
4. generate_feature_file()   – call the OpenAI API and return Gherkin text
5. build_prompt()            – (internal) assemble the LLM prompt
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

load_dotenv()

# ---------------------------------------------------------------------------
# Column-name aliases (all lower-case keys)
# ---------------------------------------------------------------------------
_COLUMN_ALIASES: dict[str, list[str]] = {
    "id": ["test case id", "tc id", "id", "test id", "testcaseid"],
    "name": ["test case name", "test name", "title", "name", "scenario"],
    "feature": ["module", "feature", "component", "feature name"],
    "given": ["preconditions", "pre-conditions", "given", "pre condition"],
    "when": ["test steps", "steps", "when", "actions"],
    "then": ["expected result", "expected results", "then", "expected"],
    "priority": ["priority"],
    "tags": ["tags", "labels", "tag"],
}

GUIDELINES_PATH = Path(__file__).parent / "guidelines.md"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def load_excel(file: Any) -> pd.DataFrame:
    """
    Read an Excel file (.xlsx / .xls) and return the first sheet as a
    DataFrame.

    Parameters
    ----------
    file : file-like object or path
        Anything accepted by ``pd.read_excel``.

    Returns
    -------
    pd.DataFrame
    """
    df = pd.read_excel(file, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def parse_test_cases(df: pd.DataFrame) -> list[dict[str, str]]:
    """
    Normalise column names using ``_COLUMN_ALIASES`` and return a list of
    test-case dicts with canonical keys:
    ``id``, ``name``, ``feature``, ``given``, ``when``, ``then``,
    ``priority``, ``tags``.

    Missing columns are silently omitted from each dict.
    """
    # Build mapping: original_col_name -> canonical_key
    col_map: dict[str, str] = {}
    lower_cols = {c.lower(): c for c in df.columns}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                col_map[lower_cols[alias]] = canonical
                break

    test_cases: list[dict[str, str]] = []
    for _, row in df.iterrows():
        tc: dict[str, str] = {}
        for orig_col, canonical in col_map.items():
            val = row.get(orig_col, "")
            if pd.notna(val) and str(val).strip():
                tc[canonical] = str(val).strip()
        if tc:
            test_cases.append(tc)

    return test_cases


def load_guidelines() -> str:
    """Return the contents of guidelines.md, or a minimal fallback."""
    if GUIDELINES_PATH.exists():
        return GUIDELINES_PATH.read_text(encoding="utf-8")
    return (
        "Generate valid Gherkin BDD feature files.\n"
        "Use Feature, Scenario, Given, When, Then keywords.\n"
        "Group related scenarios under the same Feature block.\n"
    )


def build_prompt(test_cases: list[dict[str, str]], guidelines: str) -> str:
    """
    Assemble the prompt sent to the LLM.

    Parameters
    ----------
    test_cases : list[dict]
        Parsed test-case records from parse_test_cases().
    guidelines : str
        The full content of guidelines.md.

    Returns
    -------
    str  – the user-message text for the chat completion.
    """
    tc_block = _format_test_cases(test_cases)
    prompt = (
        "You are an expert QA engineer specialising in BDD and Gherkin syntax.\n\n"
        "## Task\n"
        "Convert the test cases below into one or more `.feature` files following "
        "the guidelines provided.\n\n"
        "## Guidelines\n"
        f"{guidelines}\n\n"
        "## Test Cases\n"
        f"{tc_block}\n\n"
        "## Output Requirements\n"
        "- Return **only** the raw Gherkin text (no markdown code fences, no explanations).\n"
        "- Group scenarios by Feature.\n"
        "- Apply appropriate tags from the guidelines.\n"
        "- Every scenario must have at least one Given, one When, and one Then.\n"
        "- If multiple features are present, separate them clearly.\n"
    )
    return prompt


def generate_feature_file(
    test_cases: list[dict[str, str]],
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """
    Call the OpenAI Chat Completions API and return the generated Gherkin text.

    Parameters
    ----------
    test_cases : list[dict]
        Parsed test cases from parse_test_cases().
    api_key : str, optional
        OpenAI API key. Falls back to the ``OPENAI_API_KEY`` environment variable.
    model : str, optional
        OpenAI model name. Falls back to ``OPENAI_MODEL`` env var, then ``gpt-4o``.

    Returns
    -------
    str – raw Gherkin feature file content.

    Raises
    ------
    ValueError
        If no API key is available.
    RuntimeError
        If the API call fails.
    """
    if OpenAI is None:
        raise ImportError(
            "openai package is required. Install it with: pip install openai"
        )

    resolved_key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not resolved_key:
        raise ValueError(
            "OpenAI API key not found. Set the OPENAI_API_KEY environment variable "
            "or pass api_key= to generate_feature_file()."
        )

    resolved_model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
    guidelines = load_guidelines()
    prompt = build_prompt(test_cases, guidelines)

    client = OpenAI(api_key=resolved_key)
    try:
        response = client.chat.completions.create(
            model=resolved_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

    content = response.choices[0].message.content or ""
    # Strip accidental markdown code fences
    content = _strip_code_fences(content)
    return content.strip()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_test_cases(test_cases: list[dict[str, str]]) -> str:
    """Format test cases as a numbered list for the LLM prompt."""
    lines: list[str] = []
    for i, tc in enumerate(test_cases, start=1):
        lines.append(f"### Test Case {i}")
        for key, value in tc.items():
            lines.append(f"  {key.capitalize()}: {value}")
        lines.append("")
    return "\n".join(lines)


def _strip_code_fences(text: str) -> str:
    """Remove ```gherkin ... ``` or ``` ... ``` wrappers if present."""
    pattern = r"^```[a-zA-Z]*\n(.*?)```$"
    match = re.match(pattern, text.strip(), re.DOTALL)
    if match:
        return match.group(1)
    return text
