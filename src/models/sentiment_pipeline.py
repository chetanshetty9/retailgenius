import json
from typing import Any, Dict, List

from langdetect import detect

from src.data.analyzer_cache import ANALYZER as analyzer
from src.features.response_generator import generate_response
from src.features.sentiment import sentiment_analysis


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


def run_pipeline(reviews_json_path: str, mode: str = "safe") -> List[Dict[str, Any]]:
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
        lang = detect(review_text)
        print("\nCustomer feedback:", review_text)

        analyzed = sentiment_analysis(review_text, lang, mode)
        print(
            f'\nAnalysed review: \n\tSentiment:{analyzed["analysis"]["sentiment"]}\n\tkey_issues:{analyzed["analysis"]["key_issues_praise"]}\n\tSummary:{analyzed["analysis"]["summary"]}'
        )

        warning = analyzed.get("warning")
        critical_ref = analyzed.get("critical_ref")

        # --- Human-in-the-loop decision ---
        if warning or critical_ref:
            print("\nHuman review required:")
            if warning:
                print(f"Prompt injection warning: {warning}")
            if critical_ref:
                print(f"Critical review flagged: {critical_ref}")

            decision = (
                input("Do you want to proceed with response generation? (yes/no): ")
                .strip()
                .lower()
            )

            if decision != "yes":
                print("Skipping response generation.")
                print("=" * 30)
                continue  # or return if inside a function
            else:
                print("Thanks. Proceeding with response generation...")

        response = generate_response(analyzed, mode)

        # Check for the PII in response
        results = analyzer.analyze(text=response["customer_response"], language="en")
        if results:
            print("\n PII detected in generated AI response!")
            print("\nAI generated response:", response["customer_response"])

            for r in results:
                print(f"Entity: {r.entity_type}")
        else:
            print("\nNo PII detected in generated AI response!")
            print("\nAI generated response:", response["customer_response"])
            print("=" * 30)

        results.append(
            {
                "original_review": review_text,
                "analysis": analyzed["analysis"],
                "customer_response": response,
                "warning": analyzed["warning"],
            }
        )
    return results
