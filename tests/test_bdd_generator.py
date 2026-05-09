"""
tests/test_bdd_generator.py
---------------------------
Unit tests for bdd_generator.py.

Run with:
    python -m unittest discover -s tests -v
"""

import io
import textwrap
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from bdd_generator import (
    _format_test_cases,
    _strip_code_fences,
    build_prompt,
    load_guidelines,
    parse_test_cases,
)


class TestStripCodeFences(unittest.TestCase):
    """_strip_code_fences should remove markdown code fences."""

    def test_removes_gherkin_fence(self):
        text = "```gherkin\nFeature: Login\n```"
        self.assertEqual(_strip_code_fences(text), "Feature: Login\n")

    def test_removes_plain_fence(self):
        text = "```\nFeature: Login\n```"
        self.assertEqual(_strip_code_fences(text), "Feature: Login\n")

    def test_no_fence_unchanged(self):
        text = "Feature: Login\n  Scenario: Valid login"
        self.assertEqual(_strip_code_fences(text), text)

    def test_empty_string(self):
        self.assertEqual(_strip_code_fences(""), "")


class TestParseTestCases(unittest.TestCase):
    """parse_test_cases should normalise column names and return dicts."""

    def _make_df(self, data: dict) -> pd.DataFrame:
        return pd.DataFrame(data)

    def test_canonical_columns(self):
        df = self._make_df(
            {
                "Test Case ID": ["TC-001"],
                "Test Case Name": ["Valid Login"],
                "Module": ["Authentication"],
                "Preconditions": ["User is on login page"],
                "Test Steps": ["Enter valid credentials and click Login"],
                "Expected Result": ["User is redirected to dashboard"],
                "Priority": ["High"],
            }
        )
        result = parse_test_cases(df)
        self.assertEqual(len(result), 1)
        tc = result[0]
        self.assertEqual(tc["id"], "TC-001")
        self.assertEqual(tc["name"], "Valid Login")
        self.assertEqual(tc["feature"], "Authentication")
        self.assertEqual(tc["given"], "User is on login page")
        self.assertEqual(tc["when"], "Enter valid credentials and click Login")
        self.assertEqual(tc["then"], "User is redirected to dashboard")
        self.assertEqual(tc["priority"], "High")

    def test_alias_columns(self):
        df = self._make_df(
            {
                "TC ID": ["TC-002"],
                "Title": ["Invalid Login"],
                "Component": ["Auth"],
                "Steps": ["Enter wrong password"],
                "Expected": ["Error message shown"],
            }
        )
        result = parse_test_cases(df)
        self.assertEqual(len(result), 1)
        tc = result[0]
        self.assertEqual(tc["id"], "TC-002")
        self.assertEqual(tc["name"], "Invalid Login")
        self.assertEqual(tc["feature"], "Auth")

    def test_skips_empty_rows(self):
        df = self._make_df(
            {
                "Test Case Name": ["Valid Login", "", None],
                "Expected Result": ["Dashboard shown", "", None],
            }
        )
        result = parse_test_cases(df)
        # Only the first row has non-empty data
        self.assertEqual(len(result), 1)

    def test_multiple_rows(self):
        df = self._make_df(
            {
                "Test Case Name": ["TC A", "TC B", "TC C"],
                "Expected Result": ["Result A", "Result B", "Result C"],
            }
        )
        result = parse_test_cases(df)
        self.assertEqual(len(result), 3)

    def test_unknown_columns_ignored(self):
        df = self._make_df(
            {
                "Some Unknown Column": ["value"],
                "Test Case Name": ["Known TC"],
            }
        )
        result = parse_test_cases(df)
        self.assertEqual(len(result), 1)
        self.assertNotIn("some unknown column", result[0])

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = parse_test_cases(df)
        self.assertEqual(result, [])


class TestFormatTestCases(unittest.TestCase):
    """_format_test_cases should produce a readable numbered list."""

    def test_basic_formatting(self):
        tcs = [{"name": "Login", "then": "Dashboard shown"}]
        output = _format_test_cases(tcs)
        self.assertIn("### Test Case 1", output)
        self.assertIn("Login", output)
        self.assertIn("Dashboard shown", output)

    def test_multiple_cases_numbered(self):
        tcs = [{"name": "TC1"}, {"name": "TC2"}]
        output = _format_test_cases(tcs)
        self.assertIn("### Test Case 1", output)
        self.assertIn("### Test Case 2", output)

    def test_empty_list(self):
        self.assertEqual(_format_test_cases([]), "")


class TestBuildPrompt(unittest.TestCase):
    """build_prompt should include guidelines and test cases."""

    def test_contains_guidelines(self):
        tcs = [{"name": "Login test"}]
        guidelines = "Use Given/When/Then format."
        prompt = build_prompt(tcs, guidelines)
        self.assertIn("Use Given/When/Then format.", prompt)

    def test_contains_test_case_data(self):
        tcs = [{"name": "Add to cart", "then": "Cart updated"}]
        prompt = build_prompt(tcs, "guidelines here")
        self.assertIn("Add to cart", prompt)
        self.assertIn("Cart updated", prompt)

    def test_output_requirements_present(self):
        prompt = build_prompt([], "g")
        self.assertIn("Output Requirements", prompt)
        self.assertIn("Gherkin", prompt)


class TestLoadGuidelines(unittest.TestCase):
    """load_guidelines should return a non-empty string."""

    def test_returns_string(self):
        result = load_guidelines()
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


class TestGenerateFeatureFile(unittest.TestCase):
    """generate_feature_file should call OpenAI and return Gherkin text."""

    def test_raises_value_error_without_api_key(self):
        from bdd_generator import generate_feature_file

        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            with self.assertRaises(ValueError):
                generate_feature_file([{"name": "TC1"}], api_key="")

    def test_successful_generation(self):
        from bdd_generator import generate_feature_file

        fake_content = "Feature: Login\n  Scenario: Valid login\n    Given a user"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = fake_content

        with patch("bdd_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            result = generate_feature_file(
                [{"name": "Login", "then": "Dashboard shown"}],
                api_key="test-key",
                model="gpt-4o",
            )

        self.assertEqual(result, fake_content)

    def test_strips_code_fence_in_response(self):
        from bdd_generator import generate_feature_file

        raw = "```gherkin\nFeature: Login\n```"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = raw

        with patch("bdd_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai_cls.return_value = mock_client

            result = generate_feature_file(
                [{"name": "Login"}],
                api_key="test-key",
            )

        self.assertNotIn("```", result)
        self.assertIn("Feature: Login", result)

    def test_runtime_error_on_api_failure(self):
        from bdd_generator import generate_feature_file

        with patch("bdd_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("connection error")
            mock_openai_cls.return_value = mock_client

            with self.assertRaises(RuntimeError):
                generate_feature_file([{"name": "TC1"}], api_key="test-key")


if __name__ == "__main__":
    unittest.main()
