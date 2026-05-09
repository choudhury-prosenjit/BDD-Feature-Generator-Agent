# BDD Feature Generator Agent

A Python + LangGraph agent that reads Excel-based test cases and generates production-ready BDD `.feature` files in Gherkin format.

## Features

- Reads one or more Excel files with `pandas` and `openpyxl`
- Detects common test-case columns such as module, feature, title, steps, test data, expected result, priority, and type
- Normalizes and classifies positive, negative, and edge cases
- Groups related cases by module and feature
- Uses `Scenario Outline` with `Examples` when the same behavior is repeated with different data
- Removes duplicate scenarios while preserving test-case traceability
- Builds feature files through a LangGraph workflow
- Uses OpenAI when `OPENAI_API_KEY` is available, with deterministic draft generation as a safe fallback

## Project structure

```text
bdd_agent/
  main.py
  graph.py
  nodes/
    load_excel.py
    analyze_structure.py
    normalize.py
    classify.py
    scenario_design.py
    generate_gherkin.py
    validate.py
    write_files.py
  prompts/
    gherkin_prompt.py
  utils/
    excel_utils.py
    gherkin_utils.py
    duplicate_checker.py
  output/
main.py
requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set the OpenAI API key when you want LLM polishing enabled:

```bash
export OPENAI_API_KEY="your-api-key"
```

## Usage

```bash
python main.py --input ./testcases.xlsx --output ./output
```

You can also provide multiple inputs:

```bash
python main.py --input ./suite1.xlsx ./suite2.xlsx --output ./output
```

Optional model override:

```bash
python main.py --input ./testcases.xlsx --output ./output --model gpt-4.1-mini
```

## Workflow nodes

1. `load_excel_node` – validates files and loads all sheets into pandas DataFrames
2. `analyze_structure_node` – maps source columns to standard fields and identifies missing fields
3. `normalize_test_cases_node` – cleans values, splits steps, extracts test data, removes invalid rows
4. `classify_test_cases_node` – identifies positive, negative, and edge scenarios and flags duplicates
5. `scenario_design_node` – groups cases into `Scenario` or `Scenario Outline` structures
6. `gherkin_generation_node` – generates deterministic Gherkin and optionally polishes it with OpenAI
7. `validation_node` – enforces scenario uniqueness and Gherkin completeness checks
8. `write_feature_files_node` – writes safe `.feature` filenames into the output directory

## Excel input expectations

The agent looks for columns similar to these names:

- Module
- Test Case ID
- Feature / Scenario
- Test Case Title / Detailed Test Case
- Preconditions / Pre-conditions
- Test Steps
- Test Data
- Expected Result / Expected Results
- Priority
- Type

It also tolerates common aliases such as `Scenario`, `Procedure`, `Outcome`, or `Severity`.

## Output behavior

- Generates one `.feature` file per module/feature grouping
- Preserves test case IDs as traceability comments and tags
- Adds meaningful tags such as `@module_*`, `@feature_*`, `@positive`, `@negative`, `@edge`, `@regression`, and `@smoke`
- Creates `Background` when a common `Given` step appears in multiple scenarios

## Development verification

Run the lightweight unit tests:

```bash
python -m unittest discover -s tests -v
```
