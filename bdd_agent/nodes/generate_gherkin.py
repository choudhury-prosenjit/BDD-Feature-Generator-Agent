from __future__ import annotations

import os

from openai import OpenAI

from bdd_agent.prompts.gherkin_prompt import build_gherkin_prompt, GHERKIN_SYSTEM_PROMPT
from bdd_agent.utils.gherkin_utils import render_feature_document



def gherkin_generation_node(state: dict) -> dict:
    model = state.get("model", "gpt-4.1-mini")
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if api_key else None

    updated_documents = {}
    for feature_key, document in state.get("feature_documents", {}).items():
        deterministic_output = render_feature_document(document)
        generated_output = deterministic_output

        if client is not None:
            prompt = build_gherkin_prompt(document, deterministic_output)
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": GHERKIN_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                )
                polished_output = (
                    response.choices[0].message.content.strip()
                    if getattr(response, "choices", None)
                    and response.choices[0].message.content
                    else ""
                )
                if polished_output:
                    generated_output = polished_output
            except Exception:
                generated_output = deterministic_output

        document.content = generated_output
        updated_documents[feature_key] = document

    return {"feature_documents": updated_documents}
