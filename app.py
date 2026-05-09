"""
app.py
------
Streamlit UI for the BDD Feature Generator Agent.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import io
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from bdd_generator import load_excel, parse_test_cases, generate_feature_file

load_dotenv()

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BDD Feature Generator",
    page_icon="🥒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar – configuration
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("---")

    api_key_input = st.text_input(
        "OpenAI API Key",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        help="Your OpenAI API key. Can also be set via the OPENAI_API_KEY environment variable.",
    )

    model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
    default_model = os.getenv("OPENAI_MODEL", "gpt-4o")
    if default_model not in model_options:
        model_options.insert(0, default_model)

    selected_model = st.selectbox(
        "Model",
        options=model_options,
        index=model_options.index(default_model),
        help="OpenAI model to use for generation.",
    )

    st.markdown("---")
    st.markdown("### 📖 Guidelines")
    guidelines_path = Path(__file__).parent / "guidelines.md"
    if guidelines_path.exists():
        with st.expander("View BDD Guidelines", expanded=False):
            st.markdown(guidelines_path.read_text(encoding="utf-8"))
    else:
        st.warning("guidelines.md not found.")

    st.markdown("---")
    st.markdown(
        "**Need help?** See the [README](https://github.com/choudhury-prosenjit/"
        "BDD-Feature-Generator-Agent) for setup instructions.",
        unsafe_allow_html=False,
    )

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.title("🥒 BDD Feature Generator")
st.markdown(
    "Upload an Excel file containing test cases and generate a ready-to-use "
    "**Gherkin BDD feature file** in seconds."
)

# ---------------------------------------------------------------------------
# Step 1 – Upload Excel
# ---------------------------------------------------------------------------
st.header("Step 1 – Upload Test Cases Excel File")

uploaded_file = st.file_uploader(
    "Choose an Excel file (.xlsx or .xls)",
    type=["xlsx", "xls"],
    help="The file should contain columns such as Test Case ID, Test Case Name, "
         "Module/Feature, Preconditions, Test Steps, Expected Result, Priority.",
)

df = None
test_cases = None

if uploaded_file is not None:
    try:
        df = load_excel(uploaded_file)
        test_cases = parse_test_cases(df)
        st.success(
            f"✅ File loaded successfully: **{uploaded_file.name}** "
            f"({len(df)} rows, {len(df.columns)} columns)"
        )
    except Exception as exc:
        st.error(f"❌ Failed to read the Excel file: {exc}")
        df = None

# ---------------------------------------------------------------------------
# Step 2 – Preview data
# ---------------------------------------------------------------------------
if df is not None:
    st.header("Step 2 – Preview Test Cases")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{len(df)} test case(s) found**")
    with col2:
        show_all = st.checkbox("Show all rows", value=False)

    display_df = df if show_all else df.head(10)
    st.dataframe(display_df, use_container_width=True)

    if not show_all and len(df) > 10:
        st.caption(f"Showing 10 of {len(df)} rows. Check 'Show all rows' to see everything.")

    # Column mapping summary
    with st.expander("🗂️ Detected column mapping", expanded=False):
        if test_cases:
            detected_keys = set()
            for tc in test_cases:
                detected_keys.update(tc.keys())
            if detected_keys:
                st.markdown("The following fields were detected in your file:")
                for k in sorted(detected_keys):
                    st.markdown(f"- `{k}`")
            else:
                st.warning(
                    "No recognised columns were found. The generator will use "
                    "raw row data. For best results, use column headers described "
                    "in the guidelines."
                )
        else:
            st.warning("No test cases could be parsed.")

# ---------------------------------------------------------------------------
# Step 3 – Generate BDD Feature File
# ---------------------------------------------------------------------------
if df is not None and test_cases is not None:
    st.header("Step 3 – Generate BDD Feature File")

    if not api_key_input:
        st.warning(
            "⚠️ No OpenAI API key provided. Enter your key in the sidebar before generating."
        )

    generate_btn = st.button(
        "🚀 Generate Feature File",
        disabled=not api_key_input,
        use_container_width=True,
        type="primary",
    )

    if generate_btn:
        if not test_cases:
            st.error("No test cases found in the uploaded file. Please check your Excel format.")
        else:
            with st.spinner("🤖 Generating BDD feature file… this may take a few seconds."):
                try:
                    feature_content = generate_feature_file(
                        test_cases,
                        api_key=api_key_input,
                        model=selected_model,
                    )
                    st.session_state["feature_content"] = feature_content
                    st.session_state["source_filename"] = Path(uploaded_file.name).stem
                except ValueError as exc:
                    st.error(f"Configuration error: {exc}")
                except RuntimeError as exc:
                    st.error(f"Generation failed: {exc}")
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

# ---------------------------------------------------------------------------
# Step 4 – View & Download
# ---------------------------------------------------------------------------
if "feature_content" in st.session_state and st.session_state["feature_content"]:
    st.header("Step 4 – View & Download Feature File")

    feature_content: str = st.session_state["feature_content"]
    source_name: str = st.session_state.get("source_filename", "output")

    st.success("✅ BDD feature file generated successfully!")

    st.code(feature_content, language="gherkin")

    download_filename = f"{source_name}.feature"
    st.download_button(
        label="⬇️ Download .feature file",
        data=feature_content.encode("utf-8"),
        file_name=download_filename,
        mime="text/plain",
        use_container_width=True,
    )

    # Token / size info
    lines = feature_content.count("\n") + 1
    scenarios = feature_content.count("Scenario")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Lines", lines)
    col_b.metric("Scenarios", scenarios)
    col_c.metric("File size", f"{len(feature_content.encode('utf-8'))} bytes")

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "BDD Feature Generator Agent · Powered by OpenAI · "
    "Follow the guidelines in the sidebar for best results."
)
