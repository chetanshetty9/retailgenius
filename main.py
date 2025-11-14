# main.py

import builtins
import os
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv

from src.models.sentiment_pipeline import run_pipeline

# Override input globally
builtins.input = lambda _: "yes"


def main() -> None:
    """
    Main entry point for running the review analysis pipeline.

    Loads reviews from a JSON file, runs sentiment analysis and response
    generation, and prints the results.
    """
    load_dotenv()  # Load .env file
    MODE = os.getenv("MODE", "safe")
    print(f"\nRunning in {MODE.upper()} mode")

    input_path = os.getenv("INPUT_PATH")  # Update path to your reviews JSON file
    results: List[Dict] = run_pipeline(input_path, MODE)

    # df = pd.DataFrame(results)
    # df.to_csv("data/processed/safe_review_response.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
