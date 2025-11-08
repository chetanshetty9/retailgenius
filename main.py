# main.py

from typing import Dict, List

from src.models.sentiment_pipeline import run_pipeline


def main() -> None:
    """
    Main entry point for running the review analysis pipeline.

    Loads reviews from a JSON file, runs sentiment analysis and response
    generation, and prints the results.
    """
    input_path = "data/raw/reviews.json"  # Update path to your reviews JSON file
    results: List[Dict] = run_pipeline(input_path)

    print("\n=== Results ===")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
