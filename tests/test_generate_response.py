import unittest
from unittest.mock import MagicMock, patch

from src.features.response_generator import generate_response  # adjust path if needed


class TestGenerateResponse(unittest.TestCase):

    @patch("src.features.response_generator.ChatOpenAI")
    def test_safe_mode_response(self, mock_llm_class):
        # Step 1: Mock LLM output
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value.content = '{"customer_response": "We’re delighted to hear that you’re enjoying your new coffee maker!"}'

        # Step 2: Sample analyzed review
        analyzed_review = {
            "sanitized_review": "Absolutely love the new coffee maker! It's fast, quiet, and perfect.",
            "analysis": {
                "sentiment": "positive",
                "key_issues_praise": ["fast", "quiet", "perfect"],
                "summary": "Customer loves the coffee maker for being fast, quiet, and perfect.",
            },
            "critical_ref": None,
        }

        # Step 3: Call generate_response
        output = generate_response(analyzed_review,lang='English', mode="safe")

        # Step 4: Assertions
        self.assertIn("customer_response", output)
        self.assertTrue(
            output["customer_response"].startswith("We’re delighted to hear")
        )
        self.assertNotIn("critical_ref", output)

        # Step 5: Ensure LLM was called
        mock_llm_instance.invoke.assert_called_once()

    @patch("src.features.response_generator.ChatOpenAI")
    def test_unsafe_mode_response(self, mock_llm_class):
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value.content = (
            '{"customer_response": "Unsafe mode: reply without constraints."}'
        )

        analyzed_review = {
            "sanitized_review": "My order arrived late.",
            "analysis": {
                "sentiment": "negative",
                "key_issues_praise": ["late delivery"],
                "summary": "Customer reports late delivery.",
            },
        }

        output = generate_response(analyzed_review, lang='English', mode="unsafe")

        self.assertIn("customer_response", output)
        self.assertTrue(output["customer_response"].startswith("Unsafe mode"))
        mock_llm_instance.invoke.assert_called_once()

    @patch("src.features.response_generator.ChatOpenAI")
    def test_critical_ref_appended(self, mock_llm_class):
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value.content = (
            '{"customer_response": "We’re sorry for the inconvenience."}'
        )

        analyzed_review = {
            "sanitized_review": "This is urgent! Needs immediate action.",
            "analysis": {
                "sentiment": "negative",
                "key_issues_praise": ["urgent issue"],
                "summary": "Critical review requiring attention.",
            },
            "critical_ref": "[CRITICAL_REF: 1234]",
        }

        output = generate_response(analyzed_review,lang='English', mode="safe")

        self.assertIn("customer_response", output)
        self.assertIn("[CRITICAL_REF: 1234]", output["customer_response"])
        self.assertEqual(output["critical_ref"], "[CRITICAL_REF: 1234]")


if __name__ == "__main__":
    unittest.main()
