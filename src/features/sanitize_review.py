import re
import uuid
from typing import Any, Dict, List, Optional, Tuple


def print_colored_pii(text: str) -> None:
    """
    Print text with PII highlighted in red.

    Args:
        text (str): Text that may contain PII.

    Returns:
        None
    """
    colored = re.sub(r"(<[^>]*>)", lambda m: "\033[31m" + m.group(1) + "\033[0m", text)
    print("\nSafe text:", colored)


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
        "coupon" "system prompt",
        "jailbreak",
        "override",
        "disregard",
    ]

    if additional_forbidden:
        forbidden_phrases += additional_forbidden

    for phrase in forbidden_phrases:
        if phrase.lower() in text.lower():
            warning = f" Potential unsafe content detected: '{phrase}'"
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
