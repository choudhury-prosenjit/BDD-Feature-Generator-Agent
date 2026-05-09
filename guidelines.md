# BDD Feature File Generation Guidelines

## Overview
These guidelines define how test cases from an Excel file should be translated into
Behaviour-Driven Development (BDD) feature files written in Gherkin syntax.

---

## 1. Feature File Structure

```gherkin
Feature: <Feature Name>
  <Optional feature description (one or two sentences)>

  Background: (optional – shared pre-conditions for all scenarios in the feature)
    Given ...

  @tag1 @tag2
  Scenario: <Scenario title>
    Given <initial context>
    When  <action taken>
    Then  <expected outcome>
    And   <additional outcome> (optional)

  @tag1 @examples
  Scenario Outline: <Parameterised scenario title>
    Given <initial context with <parameter>>
    When  <action with <parameter>>
    Then  <outcome with <expected_result>>

    Examples:
      | parameter | expected_result |
      | value1    | result1         |
      | value2    | result2         |
```

---

## 2. Naming Conventions

| Element             | Convention                                                        |
|---------------------|-------------------------------------------------------------------|
| Feature name        | Title-case noun phrase matching the module or component           |
| Scenario title      | Short, imperative sentence describing a single behaviour          |
| Step text           | Plain English; no technical jargon unless unavoidable             |
| Tags                | Lowercase, hyphen-separated (e.g. `@smoke`, `@regression`)        |

---

## 3. Step Writing Rules

1. **Given** – establishes context (state of the system before the actor acts).
2. **When** – describes the action or event triggered by the actor.
3. **Then** – describes the observable outcome / assertion.
4. **And / But** – continues the previous keyword; do **not** start a scenario with And/But.
5. Keep steps atomic: one action or assertion per step.
6. Use active voice and present tense.
7. Avoid UI-level details (e.g. "click button") unless the feature is explicitly a UI feature.
8. Parameterise repeated scenarios using **Scenario Outline + Examples**.

---

## 4. Tags

Apply the following standard tags where applicable:

| Tag           | When to use                                             |
|---------------|---------------------------------------------------------|
| `@smoke`      | Critical path / happy-path scenarios                    |
| `@regression` | Scenarios covering previously reported defects          |
| `@negative`   | Scenarios that verify error handling / invalid input    |
| `@wip`        | Work-in-progress scenarios (do not run in CI)           |
| `@high`       | High-priority test case                                 |
| `@medium`     | Medium-priority test case                               |
| `@low`        | Low-priority test case                                  |

You may also use the **Test Case ID** from the Excel as a tag (e.g. `@TC-001`).

---

## 5. Excel Input Column Mapping

The generator recognises the following column headers (case-insensitive):

| Excel Column Header Variants              | Maps To          |
|-------------------------------------------|------------------|
| `test case id`, `id`, `tc id`             | Scenario tag     |
| `test case name`, `test name`, `title`    | Scenario title   |
| `module`, `feature`, `component`          | Feature name     |
| `preconditions`, `pre-conditions`, `given`| Given steps      |
| `test steps`, `steps`, `when`             | When steps       |
| `expected result`, `expected`, `then`     | Then steps       |
| `priority`                                | Priority tag     |
| `tags`, `labels`                          | Additional tags  |

If a column is absent, the generator will infer the step from the test-case description.

---

## 6. Quality Rules

- Every scenario must have **at least one** Given, one When, and one Then step.
- Scenario titles must be unique within a feature.
- Avoid vague phrases such as "it works" or "it should work".
- Do not duplicate test steps across Given/When/Then; each block has a distinct role.
- Group related scenarios under the same `Feature:` block.
- Use `Background:` only when the same Given step(s) appear in **every** scenario of the feature.

---

## 7. Output Format

- File extension: `.feature`
- Encoding: UTF-8
- Indentation: 2 spaces
- Blank line between scenarios
- Feature description (if provided) indented 2 spaces below the `Feature:` keyword
