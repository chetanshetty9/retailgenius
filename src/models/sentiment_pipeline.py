import json
from typing import Any, Dict, List

import pandas as pd

from src.features.analyzer_anonymiser import tilbury_sentiment_analysis
from src.features.response_generator import generate_response


def load_json(path: str) -> Dict[str, Any]:
    """
    Load a JSON file from the given path.

    Args:
        path (str): Path to the JSON file.

    Returns:
        dict: Parsed JSON content.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_pipeline(reviews_json_path: str) -> List[Dict[str, Any]]:
    """
    Run the end-to-end sentiment analysis and response generation pipeline.

    Steps:
    1. Load reviews from JSON.
    2. Analyze each review using tilbury_sentiment_analysis.
    3. Generate customer response using generate_response.
    4. Store results in a CSV file.

    Args:
        reviews_json_path (str): Path to the reviews JSON file.

    Returns:
        List[Dict[str, Any]]: List of processed reviews with analysis and response.
    """
    print("\n=== Processing reviews ===")
    data = load_json(reviews_json_path)
    results: List[Dict[str, Any]] = []

    for review in data.get("reviews", []):
        review_text = review.get("review_text", "")
        analyzed = tilbury_sentiment_analysis(review_text)
        response = generate_response(analyzed)

        results.append(
            {
                "original_review": review_text,
                "analysis": analyzed["analysis"],
                "customer_response": response,
                "warning": analyzed["warning"],
            }
        )

    df = pd.DataFrame(results)
    df.to_csv("data/processed/review_response.csv", index=False, encoding="utf-8")
    return results
