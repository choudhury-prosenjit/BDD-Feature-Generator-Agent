from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

STANDARD_FIELD_ALIASES = {
    "module": ["Module", "component", "domain", "area"],
    "feature": ["Feature", "feature name", "user story", "capability", "Scenario"],
    "test_case_id": ["test case id", "testcase id", "tc id", "id", "case id"],
    "title": ["Detailed Test Case", "test case title", "title", "test name"],
    "preconditions": ["Pre-conditions", "preconditions", "precondition", "pre conditions", "prerequisite"],
    "steps": ["Test Steps", "steps", "action steps", "procedure"],
    "test_data": ["test data", "data", "input data"],
    "expected_result": ["Expected Results", "expected result", "expected", "result", "outcome"],
    "priority": ["Priority", "severity"],
    "case_type": ["Type", "case type", "test type", "classification"],
}



def load_excel_workbook(path: Path) -> dict[str, pd.DataFrame]:
    with pd.ExcelFile(path, engine="openpyxl") as excel_file:
        return {
            sheet_name: pd.read_excel(excel_file, sheet_name=sheet_name, engine="openpyxl")
            for sheet_name in excel_file.sheet_names
        }



def normalize_column_name(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(value).strip().lower())
    return re.sub(r"\s+", " ", cleaned).strip()



def detect_column_mapping(columns: list[str]) -> tuple[dict[str, str], list[str]]:
    normalized_columns = {normalize_column_name(column): column for column in columns}
    mapping: dict[str, str] = {}

    for standard_field, aliases in STANDARD_FIELD_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_column_name(alias)
            if normalized_alias in normalized_columns:
                mapping[standard_field] = normalized_columns[normalized_alias]
                break

    missing_fields = [field for field in ("module", "feature", "title", "steps", "expected_result") if field not in mapping]
    return mapping, missing_fields



def clean_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).replace("\r", "\n").strip()
    text = re.sub(r"\n+", "\n", text)
    return re.sub(r"[ \t]+", " ", text).strip()



def split_steps(value: str) -> list[str]:
    if not value:
        return []

    lines = [line.strip(" -") for line in re.split(r"\n|\d+[.)]\s*", value) if line.strip(" -")]
    if len(lines) == 1 and ";" in lines[0]:
        lines = [part.strip() for part in lines[0].split(";") if part.strip()]
    return lines



def parse_test_data(value: str) -> dict[str, str]:
    if not value:
        return {}

    pairs: dict[str, str] = {}
    for part in re.split(r"[\n;|]", value):
        if not part.strip():
            continue
        if "=" in part:
            key, raw_value = part.split("=", 1)
        elif ":" in part:
            key, raw_value = part.split(":", 1)
        else:
            continue
        cleaned_key = normalize_column_name(key).replace(" ", "_")
        pairs[cleaned_key] = clean_text(raw_value)
    return pairs



def normalize_record(workbook_path: str, sheet_name: str, row: dict[str, Any], column_mapping: dict[str, str]) -> dict[str, Any] | None:
    def mapped_value(field: str) -> str:
        column = column_mapping.get(field)
        return clean_text(row.get(column, "")) if column else ""

    title = mapped_value("title")
    steps_text = mapped_value("steps")
    expected_result = mapped_value("expected_result")
    if not any([title, steps_text, expected_result]):
        return None

    module = mapped_value("module") or "General"
    feature = mapped_value("feature") or module
    steps = split_steps(steps_text)
    preconditions = split_steps(mapped_value("preconditions"))
    test_data_raw = mapped_value("test_data")
    priority = mapped_value("priority")
    case_type = mapped_value("case_type")
    test_case_id = mapped_value("test_case_id")

    return {
        "source_workbook": workbook_path,
        "source_sheet": sheet_name,
        "module": module,
        "feature": feature,
        "test_case_id": test_case_id,
        "title": title or expected_result or "Unnamed scenario",
        "preconditions": preconditions,
        "steps": steps,
        "test_data": parse_test_data(test_data_raw),
        "test_data_raw": test_data_raw,
        "expected_result": expected_result,
        "priority": priority,
        "case_type": case_type,
    }
