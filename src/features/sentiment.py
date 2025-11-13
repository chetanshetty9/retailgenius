import json
import pickle
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities.engine import OperatorConfig

from src.data.analyzer_cache import ANALYZER as analyzer
from src.features.sanitize_review import (
    generate_critical_ref,
    is_critical_review,
    print_colored_pii,
    sanitize_input,
)


def sentiment_analysis(
    review_text: str, lang: str, mode: str = "safe"
) -> Dict[str, Any]:
    """
    Analyze a customer review with optional SAFE/UNSAFE mode.

    Args:
        review_text (str): Raw customer review.
        mode (str): Either "safe" (default, with protections) or "unsafe" (PII + CRITICAL_REF bypassed).

    Returns:
        dict: Contains sanitized review, analysis result, critical reference, and any warnings.
    """

    # UNSAFE MODE — Bypasses protections

    if mode.lower() == "unsafe":
        print("\n PII redaction and CRITICAL_REF safeguards are DISABLED.")
        llm = ChatOpenAI()
        messages = [
            SystemMessage(
                content=(
                    "You are a helpful assistant that analyzes customer reviews. "
                    "Use only the information explicitly provided in the customer review — do not add, assume, or infer any details not stated. "
                    f"The following customer review is written in language: {lang}. Please respond empathetically in the SAME LANGUAGE ({lang}"
                    "Extract sentiment (positive, negative, neutral), key issues/praises "
                    "(list of strings), and a 1–2 sentence summary. "
                    "Always respond in valid JSON format with keys: sentiment, "
                    "key_issues_praise, summary."
                )
            ),
            HumanMessage(content=f'Review:\n"""{review_text}"""'),
        ]
        response = llm.invoke(messages)

        try:
            output = json.loads(response.content.strip())
        except Exception:
            output = {"sentiment": "unknown", "summary": response.content.strip()}
        return {
            "sanitized_review": review_text,
            "analysis": output,
            "critical_ref": None,  # Disabled
            "warning": "Unsafe mode active — no PII redaction or safeguards applied.",
        }

    # SAFE MODE — All protections active

    anonymizer = AnonymizerEngine()
    operators = {
        "ADDRESS": OperatorConfig("replace", {"new_value": "<ADDRESS>"}),
        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE_NUMBER>"}),
        "ORDER_ID": OperatorConfig("replace", {"new_value": "<ORDER_ID>"}),
    }

    results = analyzer.analyze(text=review_text, language="en")
    anonymized = anonymizer.anonymize(
        text=review_text, analyzer_results=results, operators=operators
    )
    print_colored_pii(anonymized.text)

    # Step 1: Anonymize text
    clean_text = anonymized.text

    # Step 2: Sanitize input
    safe_text, warning = sanitize_input(clean_text)

    # Step 3: Detect critical review
    if is_critical_review(safe_text):
        critical_ref = generate_critical_ref()
        skip_detailed_analysis = True
    else:
        critical_ref = None
        skip_detailed_analysis = False

    # Step 4: Create message chain for LLM
    system_content = (
        "You are a helpful assistant that analyzes customer reviews. "
        f"The following customer review is written in {lang}. Please respond empathetically in the SAME LANGUAGE ({lang}"
        "Extract sentiment (positive, negative, neutral), key issues/praises (list of strings), "
        f"and a 1–2 sentence summary in {lang}. "
        "Always respond in valid JSON format exactly like this:\n\n"
        "{\n"
        '  "sentiment": "positive" | "negative" | "neutral",\n'
        '  "key_issues_praise": ["issue1", "issue2", ...],\n'
        '  "summary": "summary"\n'
        "}\n\n"
        "Do not include any other text or commentary outside this JSON."
    )
    if skip_detailed_analysis:
        system_content += "\nFor critical reviews, provide an abbreviated analysis."

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=f'Review:\n"""{safe_text}"""'),
    ]

    # Run LLM
    llm = ChatOpenAI()
    response = llm.invoke(messages)
    output = json.loads(response.content.strip())

    # Return all analysis
    return {
        "sanitized_review": safe_text,
        "analysis": output,
        "critical_ref": critical_ref,
        "warning": warning,
    }
