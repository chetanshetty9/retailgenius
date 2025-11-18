import json
import os

from dotenv import load_dotenv


def load_dataset():
    input_path = os.getenv("INPUT_PATH")  # Update path to your reviews JSON file
    print("\n=== Processing reviews ===")

    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)
