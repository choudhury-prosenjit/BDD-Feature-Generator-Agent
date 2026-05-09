"""Streamlit UI for the BDD Feature Generator Agent.

Launch with:
    streamlit run app.py
"""
from __future__ import annotations

import os
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

import streamlit as st

from bdd_agent.graph import run_agent

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BDD Feature Generator",
    page_icon="🥒",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar – settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    openai_key = st.text_input(
        "OpenAI API Key (optional)",
        type="password",
        help="Leave blank to use deterministic Gherkin generation without an LLM.",
    )

    model = st.selectbox(
        "OpenAI model",
        options=["gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        index=0,
        help="Only used when an API key is provided.",
    )

    st.markdown("---")
    st.markdown(
        "**Excel column expectations**\n\n"
        "- Test Case ID\n"
        "- Module\n"
        "- Scenario\n"
        "- Pre-conditions\n"
        "- Detailed Test Case\n"
        "- Test Steps\n"
        "- Expected Results\n"
        "- Priority\n"
        "- Type"
    )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
st.title("🥒 BDD Feature Generator")
st.markdown(
    "Upload one or more Excel files containing test cases. "
    "The agent will analyse the rows and produce Gherkin `.feature` files "
    "that you can download as a ZIP archive."
)

uploaded_files = st.file_uploader(
    "Upload Excel file(s)",
    type=["xlsx", "xls"],
    accept_multiple_files=True,
    help="Each file may contain multiple sheets. All sheets are processed.",
)

generate_btn = st.button(
    "🚀 Generate BDD Feature Files",
    disabled=not uploaded_files,
    type="primary",
)

if generate_btn and uploaded_files:
    # Optionally inject the API key into the environment for this run
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    elif "OPENAI_API_KEY" in os.environ and not openai_key:
        # Don't override a key that was already set in the environment
        pass

    with st.spinner("Running the BDD agent pipeline…"):
        # Write uploads to a temporary directory so the agent can read them
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_dir = tmp_path / "input"
            output_dir = tmp_path / "output"
            input_dir.mkdir()
            output_dir.mkdir()

            input_paths: list[str] = []
            for uploaded in uploaded_files:
                dest = input_dir / uploaded.name
                dest.write_bytes(uploaded.read())
                input_paths.append(str(dest))

            try:
                result = run_agent(
                    input_paths=input_paths,
                    output_dir=str(output_dir),
                    model=model,
                )

                written_files: list[str] = result.get("written_files", [])
                validation_errors: list[str] = result.get("validation_errors", [])

                # -------------------------------------------------------
                # Results
                # -------------------------------------------------------
                if validation_errors:
                    with st.expander("⚠️ Validation warnings", expanded=False):
                        for err in validation_errors:
                            st.warning(err)

                if not written_files:
                    st.error(
                        "No feature files were generated. "
                        "Check that your Excel file contains the expected columns."
                    )
                else:
                    st.success(f"✅ Generated **{len(written_files)}** feature file(s).")

                    # Build a ZIP in memory
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for fp in written_files:
                            zf.write(fp, Path(fp).name)
                    zip_buffer.seek(0)

                    st.download_button(
                        label="⬇️ Download all feature files (.zip)",
                        data=zip_buffer,
                        file_name="bdd_features.zip",
                        mime="application/zip",
                    )

                    # Preview each file
                    st.markdown("---")
                    st.subheader("📄 Feature file preview")
                    for fp in sorted(written_files):
                        feature_name = Path(fp).name
                        content = Path(fp).read_text(encoding="utf-8")
                        with st.expander(feature_name, expanded=False):
                            st.code(content, language="gherkin")

            except Exception as exc:  # noqa: BLE001
                st.error(f"Agent error: {exc}")
                st.exception(exc)
