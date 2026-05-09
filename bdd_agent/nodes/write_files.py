from __future__ import annotations

from pathlib import Path

from bdd_agent.utils.gherkin_utils import safe_filename



def write_feature_files_node(state: dict) -> dict:
    output_dir = Path(state["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)

    written_files: list[str] = []
    for document in state.get("feature_documents", {}).values():
        filename = safe_filename(f"{document.module}_{document.feature}")
        output_path = output_dir / f"{filename}.feature"
        output_path.write_text(document.content, encoding="utf-8")
        written_files.append(str(output_path))

    return {"written_files": written_files}
