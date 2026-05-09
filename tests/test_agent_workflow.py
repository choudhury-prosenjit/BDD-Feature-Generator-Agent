from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from bdd_agent.graph import run_agent
from bdd_agent.nodes.generate_gherkin import gherkin_generation_node
from bdd_agent.utils.gherkin_utils import FeatureDocument, ScenarioDocument


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

    def test_supports_requested_exact_excel_columns(self) -> None:
        self._write_excel(
            pd.DataFrame(
                [
                    {
                        "Test Case ID": "ZELLE-001",
                        "Module": "Payments",
                        "Scenario": "Zelle Transfer",
                        "Pre-conditions": "the customer is authenticated",
                        "Detailed Test Case": "Transfer funds to an enrolled recipient",
                        "Test Steps": "select recipient\nenter amount\nconfirm transfer",
                        "Expected Results": "the transfer should complete successfully",
                        "Priority": "High",
                        "Type": "positive",
                    }
                ]
            )
        )

        result = run_agent([str(self.input_file)], str(self.output_dir))

        self.assertFalse(result["validation_errors"])
        self.assertEqual(len(result["written_files"]), 1)

        feature_content = Path(result["written_files"][0]).read_text(encoding="utf-8")
        self.assertIn("Feature: Zelle Transfer", feature_content)
        self.assertIn("Scenario: Transfer funds to an enrolled recipient", feature_content)
        self.assertIn("Given the customer is authenticated", feature_content)
        self.assertIn("Then the transfer should complete successfully", feature_content)
        self.assertIn("# Traceability: ZELLE-001", feature_content)

    def test_gherkin_generation_uses_openai_chat_completions_when_available(self) -> None:
        document = FeatureDocument(
            module="Billing",
            feature="Refunds",
            tags=["@module_billing", "@feature_refunds"],
            scenarios=[
                ScenarioDocument(
                    title="Refund a completed payment",
                    tags=["@positive"],
                    traceability_ids=["TC-501"],
                    steps=[
                        "Given the payment exists",
                        "When the agent requests a refund",
                        "Then the refund should be created",
                    ],
                    scenario_type="Scenario",
                )
            ],
        )
        mocked_client = MagicMock()
        mocked_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Feature: Refunds\n"))]
        )

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=False):
            with patch("bdd_agent.nodes.generate_gherkin.OpenAI", return_value=mocked_client) as openai_cls:
                result = gherkin_generation_node(
                    {
                        "model": "gpt-4.1-mini",
                        "feature_documents": {"billing::refunds": document},
                    }
                )

        openai_cls.assert_called_once_with(api_key="test-key")
        mocked_client.chat.completions.create.assert_called_once()
        self.assertEqual(result["feature_documents"]["billing::refunds"].content, "Feature: Refunds")


if __name__ == "__main__":
    unittest.main()
