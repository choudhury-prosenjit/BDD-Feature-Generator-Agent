from __future__ import annotations

from bdd_agent.utils.excel_utils import detect_column_mapping



def analyze_structure_node(state: dict) -> dict:
    analysis: list[dict] = []

    for workbook_path, sheets in state.get("raw_sheets", {}).items():
        for sheet_name, dataframe in sheets.items():
            mapping, missing_fields = detect_column_mapping(dataframe.columns.tolist())
            analysis.append(
                {
                    "workbook_path": workbook_path,
                    "sheet_name": sheet_name,
                    "column_mapping": mapping,
                    "missing_fields": missing_fields,
                }
            )

    return {"structure_analysis": analysis}
