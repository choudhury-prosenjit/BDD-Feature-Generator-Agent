from __future__ import annotations

from pathlib import Path

from bdd_agent.utils.excel_utils import load_excel_workbook



def load_excel_node(state: dict) -> dict:
    raw_sheets: dict[str, dict[str, object]] = {}

    for input_path in state.get("input_paths", []):
        path = Path(input_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Excel input file not found: {path}")
        raw_sheets[str(path)] = load_excel_workbook(path)

    return {"raw_sheets": raw_sheets}
