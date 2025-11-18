# main.py

import builtins
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

# Override input globally for automated execution (prevents blocking input prompts)
builtins.input = lambda _: "no"


class State(TypedDict):
    # Core pipeline fields
    review: str                      # Raw review text
    clean_text: str                  # Anonymized text
    safetext: str                    # Sanitized text (after injection removal)
    warning: Literal["yes", "no"]    # Prompt injection or unsafe content detected
    critical_ref_num: Optional[str]  # Critical reference ID from escalation logic

    # Extracted insights
    sentiment: Optional[str]
    key_issues: List[str]
    summary: Optional[str]

    # Meta fields
    lang: str
    mode: str

    # Final generated response to customer
    customer_response: Dict[str, Any]

    # Human-in-the-loop decision (yes/no)
    human_decision: Literal["yes", "no"]


def main() -> None:
    """
    Main entry point for running the review analysis pipeline.

    Loads reviews, constructs the LangGraph workflow, executes the pipeline,
    prints results, and saves them to CSV.
    """

    load_dotenv()
    MODE = os.getenv("MODE", "safe")
    print(f"\nRunning in {MODE.upper()} mode")

    # Initialize the LangGraph state machine with the TypedDict schema
    graph = StateGraph(State)

    # --- Register pipeline nodes ---
    graph.add_node("sentiment_analysis", sentiment_analysis)
    graph.add_node("check_critical_condition", check_critical_condition)
    graph.add_node("human_in_loop", human_in_loop)
    graph.add_node("create_jira_ticket", create_jira_ticket)
    graph.add_node("generate_response", generate_response)
    graph.add_node("human_in_loop_decision", human_in_loop_decision)

    # --- Define transitions between pipeline steps ---
    graph.add_edge(START, "sentiment_analysis")

    # branching after sentiment analysis → critical handling logic
    graph.add_conditional_edges("sentiment_analysis", check_critical_condition)

    # branching after human review decision → ticket or safe response
    graph.add_conditional_edges("human_in_loop", human_in_loop_decision)

    # terminal nodes
    graph.add_edge("create_jira_ticket", END)
    graph.add_edge("generate_response", END)

    # compile workflow
    res = graph.compile()

    # load review dataset
    data = load_dataset()

    results = []

    # --- Run pipeline for each review ---
    for review in data["reviews"]:
        review_text = review.get("review_text", "")

        # initial state values required by LangGraph
        iteration = res.invoke(
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
                "mode": "safe",
                "customer_response": "",
            }
        )

        # pretty-print result for each review
        print(
            f"""\nAnalysed review:\n
Review: {iteration.get("review")}

Clean Text: {iteration.get("clean_text")}

Safe Text: {iteration.get("safetext")}

Warning: {iteration.get("warning")}

Critical Ref Number: {iteration.get("critical_ref_num")}

Sentiment: {iteration.get("sentiment")}

Key Issues: {iteration.get("key_issues")}

Summary: {iteration.get("summary")}

Language: {iteration.get("lang")}

Mode: {iteration.get("mode")}

Customer Response: {iteration.get("customer_response")}
"""
        )
        print("=" * 120)

        results.append(iteration)

    # save all pipeline outputs
    df = pd.DataFrame(results)
    df.to_csv("data/processed/safe_review_response.csv", index=False, encoding="utf-8")


if __name__ == "__main__":
    main()
