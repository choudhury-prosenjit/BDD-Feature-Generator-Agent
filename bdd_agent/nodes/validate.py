from __future__ import annotations

from bdd_agent.utils.gherkin_utils import validate_feature_document



def validation_node(state: dict) -> dict:
    validation_errors: list[str] = []
    for document in state.get("feature_documents", {}).values():
        validation_errors.extend(validate_feature_document(document))

    return {"validation_errors": validation_errors}
