import unittest
from unittest.mock import patch, MagicMock

# Import your function
from src.features.analyzer_anonymiser import tilbury_sentiment_analysis

class TestTilburySentimentAnalysis(unittest.TestCase):
    @patch("src.features.analyzer_anonymiser.ChatOpenAI")  # Mock the LLM class
    def test_positive_review_safe_mode(self, mock_llm_class):
        # Step 1: Prepare the mock LLM
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value.content = (
            '{"sentiment": "positive", '
            '"key_issues_praise": ["fast", "quiet", "perfect cup"], '
            '"summary": "The customer absolutely loves the new coffee maker for being fast, quiet, and making the perfect cup every time."}'
        )

        # Step 2: Input review
        review_text = (
            "Absolutely love the new coffee maker! It's fast, quiet, and makes the perfect cup every time. Thanks, Jane Doe!"
        )

        # Step 3: Call the function in SAFE mode
        result = tilbury_sentiment_analysis(review_text, mode="safe")

        # Step 4: Check structure
        self.assertIn("sanitized_review", result)
        self.assertIn("analysis", result)
        self.assertIn("critical_ref", result)
        self.assertIn("warning", result)

        # Step 5: Check analysis content
        analysis = result["analysis"]
        self.assertEqual(analysis["sentiment"], "positive")
        self.assertEqual(analysis["key_issues_praise"], ["fast", "quiet", "perfect cup"])
        self.assertIn("loves the new coffee maker", analysis["summary"])

        # Step 6: Ensure LLM was called exactly once
        mock_llm_instance.invoke.assert_called_once()

    @patch("src.features.analyzer_anonymiser.ChatOpenAI")
    def test_critical_review_generates_ref(self, mock_llm_class):
        # LLM mock returns some valid JSON
        mock_llm_instance = MagicMock()
        mock_llm_class.return_value = mock_llm_instance
        mock_llm_instance.invoke.return_value.content = '{"sentiment": "negative", "key_issues_praise": [], "summary": "Critical issue detected."}'

        review_text = "This is urgent! Needs immediate action."

        result = tilbury_sentiment_analysis(review_text, mode="safe")

        # Critical ref should be generated
        self.assertIsNotNone(result["critical_ref"])
        self.assertTrue(result["critical_ref"].startswith("[CRITICAL_REF:"))

        # Analysis returned correctly
        self.assertEqual(result["analysis"]["sentiment"], "negative")

if __name__ == "__main__":
    unittest.main()