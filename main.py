# main.py

from typing import Dict, List

from src.models.sentiment_pipeline import run_pipeline

import os
from dotenv import load_dotenv


def main() -> None:
    """
    Main entry point for running the review analysis pipeline.

    Loads reviews from a JSON file, runs sentiment analysis and response
    generation, and prints the results.
    """
    load_dotenv()  # Load .env file
    MODE = os.getenv("MODE", "safe")
    print(f"Running in {MODE.upper()} mode")

    input_path = "data/raw/reviews.json"  # Update path to your reviews JSON file
    results: List[Dict] = run_pipeline(input_path,MODE)

    print("\n=== Results ===")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
