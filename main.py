# main.py

import os
from typing import Any, Dict, List, Literal, Optional, TypedDict

import pandas as pd
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from src.features.jira_ticket import check_critical_condition, create_jira_ticket
from src.features.load_dataset import load_dataset
from src.features.prompt_injection import human_in_loop, human_in_loop_decision
from src.features.response_generator import generate_response
from src.features.sentiment import sentiment_analysis

# -----------------------------
# TypedDict schema for LangGraph
# -----------------------------
class State(TypedDict):
    review: str
    clean_text: str
    safetext: str
    warning: Literal["yes", "no"]
    critical_ref_num: Optional[str]
    sentiment: Optional[str]
    key_issues: List[str]
    summary: Optional[str]
    lang: str
    mode: str
    customer_response: Dict[str, Any]
    human_decision: Literal["yes", "no"]

# -----------------------------
# Function for Streamlit / single review
# -----------------------------
def analyze_single_review(review_text: str) -> dict:
    """
    Run the LangGraph workflow on a single review.
    Returns the result dictionary (ready for UI display).
    """
    load_dotenv()
    MODE = os.getenv("MODE", "safe")

    # Initialize workflow
    graph = StateGraph(State)
    graph.add_node("sentiment_analysis", sentiment_analysis)
    graph.add_node("check_critical_condition", check_critical_condition)
    graph.add_node("human_in_loop", human_in_loop)
    graph.add_node("create_jira_ticket", create_jira_ticket)
    graph.add_node("generate_response", generate_response)
    graph.add_node("human_in_loop_decision", human_in_loop_decision)

    graph.add_edge(START, "sentiment_analysis")
    graph.add_conditional_edges("sentiment_analysis", check_critical_condition)
    graph.add_conditional_edges("human_in_loop", human_in_loop_decision)
    graph.add_edge("create_jira_ticket", END)
    graph.add_edge("generate_response", END)

    workflow = graph.compile()

    # Run workflow for single review
    output = workflow.invoke(
        {
            "review": review_text,
            "clean_text": "",
            "safetext": "",
            "warning": "",
            "critical_ref_num": "",
            "sentiment": "",
            "key_issues": "",
            "summary": "",
            "lang": "",
            "mode": MODE,
            "customer_response": "",
        }
    )

    return output

# -----------------------------
# Batch processing (CLI / main)
# -----------------------------
def main() -> None:
    """
    Main entry point for batch processing all reviews.
    Prints results and saves to CSV.
    """
    load_dotenv()
    MODE = os.getenv("MODE", "safe")
    print(f"\nRunning in {MODE.upper()} mode")

    # Load dataset
    data = load_dataset()
    results = []

    for i, review in enumerate(data["reviews"], start=1):
        review_text = review.get("review_text", "")
        result = analyze_single_review(review_text)

        # Pretty-print result in console
        print(f"\n--- Review {i} ---")
        print(f"Original Review: {result.get('review')}")
        print(f"Clean Text: {result.get('clean_text')}")
        print(f"Safe Text: {result.get('safetext')}")
        print(f"Warning: {result.get('warning')}")
        print(f"Critical Ref Number: {result.get('critical_ref_num')}")
        print(f"Sentiment: {result.get('sentiment')}")
        print(f"Key Issues: {result.get('key_issues')}")
        print(f"Summary: {result.get('summary')}")
        print(f"Language: {result.get('lang')}")
        print(f"Mode: {result.get('mode')}")
        print(f"Customer Response: {result.get('customer_response')}")
        print("=" * 120)

        results.append(result)

    # Save results to CSV
    df = pd.DataFrame(results)
    df.to_csv("data/processed/safe_review_response.csv", index=False, encoding="utf-8")
    print(f"\nSaved results to data/processed/safe_review_response.csv")

# -----------------------------
# Run CLI batch
# -----------------------------
if __name__ == "__main__":
    main()
