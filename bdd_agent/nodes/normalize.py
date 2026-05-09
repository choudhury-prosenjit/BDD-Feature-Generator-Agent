from __future__ import annotations

import pandas as pd

from bdd_agent.utils.excel_utils import normalize_record



def normalize_test_cases_node(state: dict) -> dict:
    normalized: list[dict] = []
    analysis_index = {
        (entry["workbook_path"], entry["sheet_name"]): entry["column_mapping"]
        for entry in state.get("structure_analysis", [])
    }

    for workbook_path, sheets in state.get("raw_sheets", {}).items():
        for sheet_name, dataframe in sheets.items():
            mapping = analysis_index.get((workbook_path, sheet_name), {})
            cleaned_frame = dataframe.dropna(how="all")
            for _, row in cleaned_frame.iterrows():
                normalized_record = normalize_record(
                    workbook_path=workbook_path,
                    sheet_name=sheet_name,
                    row=row.to_dict(),
                    column_mapping=mapping,
                )
                if normalized_record and any(normalized_record.get(field) for field in ("title", "steps", "expected_result")):
                    normalized.append(normalized_record)

    return {"normalized_test_cases": normalized}
