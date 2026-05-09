# BDD-Feature-Generator-Agent
An Agent to Generate BDD Feature file with scenarios from a Excel file with test cases

## Overview

The BDD Feature Generator Agent provides a **Streamlit web UI** that lets you:

1. **Browse & upload** an Excel file containing manual test cases.
2. **Preview** the parsed test-case data in an interactive table.
3. **Generate** a ready-to-use Gherkin `.feature` file using OpenAI and the built-in BDD guidelines.
4. **Download** the generated feature file with one click.

---

## Project Structure

```
BDD-Feature-Generator-Agent/
├── app.py                   # Streamlit UI (entry point)
├── bdd_generator.py         # Core logic: Excel parsing + LLM generation
├── guidelines.md            # BDD feature file generation guidelines
├── requirements.txt         # Python dependencies
├── sample_test_cases.xlsx   # Example Excel file to try the app
├── .env.example             # Template for environment variables
└── tests/
    └── test_bdd_generator.py  # Unit tests
```

---

## Setup

### Prerequisites

* Python 3.10+
* An [OpenAI API key](https://platform.openai.com/account/api-keys)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/choudhury-prosenjit/BDD-Feature-Generator-Agent.git
cd BDD-Feature-Generator-Agent

# 2. (Recommended) Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=<your key>
```

---

## Running the App

```bash
streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

### UI walkthrough

| Step | What to do |
|------|-----------|
| **Sidebar** | Enter your OpenAI API key and choose a model |
| **Step 1** | Upload your Excel file (`.xlsx` / `.xls`) |
| **Step 2** | Preview the parsed test cases; check the detected column mapping |
| **Step 3** | Click **Generate Feature File** |
| **Step 4** | View the Gherkin output and download the `.feature` file |

A sample file (`sample_test_cases.xlsx`) is included in the repository so you can try the app immediately.

---

## Excel File Format

The generator auto-detects common column names (case-insensitive):

| Excel column | BDD mapping |
|---|---|
| `Test Case ID` / `TC ID` / `ID` | Scenario tag |
| `Test Case Name` / `Title` / `Name` | Scenario title |
| `Module` / `Feature` / `Component` | Feature name |
| `Preconditions` / `Pre-conditions` / `Given` | Given steps |
| `Test Steps` / `Steps` / `When` | When steps |
| `Expected Result` / `Expected` / `Then` | Then steps |
| `Priority` | Priority tag |
| `Tags` / `Labels` | Additional tags |

Missing columns are gracefully handled; the LLM will infer the missing information from context.

---

## BDD Guidelines

The generation follows the rules defined in [`guidelines.md`](./guidelines.md), including:

* Gherkin **Feature / Scenario / Scenario Outline** structure
* **Given / When / Then** step writing rules
* Standard **tag** conventions (`@smoke`, `@regression`, `@negative`, etc.)
* **Scenario Outline + Examples** for data-driven tests
* Quality rules (unique titles, at least one G/W/T per scenario, etc.)

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | Your OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o` | Model used for generation |
