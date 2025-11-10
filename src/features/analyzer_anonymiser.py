import json
import pickle
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities.engine import OperatorConfig

from dotenv import load_dotenv

from src.data.analyzer_cache import ANALYZER as analyzer

def print_colored_pii(text: str) -> None:
    """
    Print text with PII highlighted in red.

    Args:
        text (str): Text that may contain PII.

    Returns:
        None
    """
    colored = re.sub(r"(<[^>]*>)", lambda m: "\033[31m" + m.group(1) + "\033[0m", text)
    print(colored)


def sanitize_input(
    text: str, additional_forbidden: Optional[List[str]] = None
) -> Tuple[str, Optional[str]]:
    """
    Sanitize text by replacing forbidden phrases with [REDACTED].

    Args:
        text (str): Input text to sanitize.
        additional_forbidden (list, optional): Extra forbidden words.

    Returns:
        tuple[str, Optional[str]]: Sanitized text and warning message if any forbidden phrases were found.
    """
    warning = None
    forbidden_phrases = [
        "ignore",
        "system prompt",
        "jailbreak",
        "override",
        "disregard",
    ]

    if additional_forbidden:
        forbidden_phrases += additional_forbidden

    for phrase in forbidden_phrases:
        if phrase.lower() in text.lower():
            warning = f" Warning: Potential unsafe content detected: '{phrase}'"
            print(warning)
            text = re.sub(re.escape(phrase), "[REDACTED]", text, flags=re.IGNORECASE)

    return text, warning


def generate_critical_ref() -> str:
    """
    Generate a unique reference ID for critical reviews.

    Returns:
        str: A critical reference string.
    """
    return f"[CRITICAL_REF: {uuid.uuid4()}]"


def is_critical_review(safe_text: str) -> bool:
    """
    Check if the review contains any critical keywords.

    Args:
        safe_text (str): Sanitized review text.

    Returns:
        bool: True if the review is critical, False otherwise.
    """
    CRITICAL_KEYWORDS = ["urgent", "critical", "immediate action", "ASAP"]
    lower_text = safe_text.lower()
    return any(keyword in lower_text for keyword in CRITICAL_KEYWORDS)


def tilbury_sentiment_analysis(review_text: str,mode: str = "safe") -> Dict[str, Any]:
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
        print("⚠️ Running in UNSAFE mode: PII redaction and CRITICAL_REF safeguards are DISABLED.")
        llm = ChatOpenAI()
        messages = [
            SystemMessage( 
                content = (
        "You are a helpful assistant that analyzes customer reviews. "
        "Extract sentiment (positive, negative, neutral), key issues/praises "
        "(list of strings), and a 1–2 sentence summary. "
        "Always respond in valid JSON format with keys: sentiment, "
        "key_issues_praise, summary."
        )),
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

    # --------------------------
    # SAFE MODE — All protections active
    # --------------------------
    print("Running in SAFE mode: PII protection and CRITICAL_REF safeguards enabled.")
    
    
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
    print("safe_text:", safe_text)

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
        "Extract sentiment (positive, negative, neutral), key issues/praises "
        "(list of strings), and a 1–2 sentence summary. "
        "Always respond in valid JSON format with keys: sentiment, "
        "key_issues_praise, summary."
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
