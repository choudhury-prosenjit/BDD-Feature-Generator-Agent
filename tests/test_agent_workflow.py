from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from bdd_agent.graph import run_agent


class AgentWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.input_file = self.base_path / "testcases.xlsx"
        self.output_dir = self.base_path / "output"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_excel(self, frame: pd.DataFrame) -> None:
        frame.to_excel(self.input_file, index=False)

    def test_generates_feature_file_and_groups_outline_examples(self) -> None:
        self._write_excel(
            pd.DataFrame(
                [
                    {
                        "Module": "Authentication",
                        "Feature": "Login",
                        "Test Case ID": "TC-001",
                        "Test Case Title": "Login with valid credentials",
                        "Preconditions": "the user is on the login page",
                        "Test Steps": "enter username\nenter password\nclick login",
                        "Test Data": "username=alice;password=secret1",
                        "Expected Result": "the user should be logged in successfully",
                        "Priority": "High",
                        "Type": "positive",
                    },
                    {
                        "Module": "Authentication",
                        "Feature": "Login",
                        "Test Case ID": "TC-002",
                        "Test Case Title": "Login with valid credentials",
                        "Preconditions": "the user is on the login page",
                        "Test Steps": "enter username\nenter password\nclick login",
                        "Test Data": "username=bob;password=secret2",
                        "Expected Result": "the user should be logged in successfully",
                        "Priority": "High",
                        "Type": "positive",
                    },
                    {
                        "Module": "Authentication",
                        "Feature": "Login",
                        "Test Case ID": "TC-003",
                        "Test Case Title": "Login with invalid password",
                        "Preconditions": "the user is on the login page",
                        "Test Steps": "enter username\nenter password\nclick login",
                        "Test Data": "username=alice;password=wrong",
                        "Expected Result": "an invalid credentials message should be displayed",
                        "Priority": "Medium",
                        "Type": "negative",
                    },
                ]
            )
        )

        result = run_agent([str(self.input_file)], str(self.output_dir))

        self.assertFalse(result["validation_errors"])
        self.assertEqual(len(result["written_files"]), 1)

        feature_content = Path(result["written_files"][0]).read_text(encoding="utf-8")
        self.assertIn("Feature: Login", feature_content)
        self.assertIn("Scenario Outline: Login with valid credentials", feature_content)
        self.assertIn("Examples:", feature_content)
        self.assertIn("| username | password |", feature_content)
        self.assertIn("@positive", feature_content)
        self.assertIn("@negative", feature_content)
        self.assertIn("# Traceability: TC-001", feature_content)
        self.assertIn("# Traceability: TC-003", feature_content)

    def test_deduplicates_identical_cases(self) -> None:
        self._write_excel(
            pd.DataFrame(
                [
                    {
                        "Module": "Catalog",
                        "Feature": "Search",
                        "Test Case ID": "TC-101",
                        "Test Case Title": "Search by product name",
                        "Preconditions": "the catalog is available",
                        "Test Steps": "enter product name\nclick search",
                        "Expected Result": "matching products should be displayed",
                    },
                    {
                        "Module": "Catalog",
                        "Feature": "Search",
                        "Test Case ID": "TC-101-DUP",
                        "Test Case Title": "Search by product name",
                        "Preconditions": "the catalog is available",
                        "Test Steps": "enter product name\nclick search",
                        "Expected Result": "matching products should be displayed",
                    },
                ]
            )
        )

        result = run_agent([str(self.input_file)], str(self.output_dir))
        feature_content = Path(result["written_files"][0]).read_text(encoding="utf-8")

        self.assertEqual(feature_content.count("Scenario:"), 1)
        self.assertNotIn("Duplicate scenario title", "\n".join(result["validation_errors"]))


if __name__ == "__main__":
    unittest.main()
