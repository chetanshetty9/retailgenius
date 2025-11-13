import json
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

few_shot_examples = [
    {
        "input": {
            "sentiment": "negative",
            "key_issues_praise": ["broken product", "poor communication"],
            "summary": (
                "The customer’s order arrived damaged and they’re frustrated "
                "with lack of response."
            ),
            "review_text": (
                "My order #<ORDER_ID> arrived broken. This is unacceptable. "
                "I've been trying to get through for <DATE_TIME>. "
                "Please have a manager call me back at <PHONE_NUMBER>."
            ),
        },
        "COT": (
            "1. Identify the sentiment as negative due to dissatisfaction.\n"
            "2. Recognize key issues: damaged product and poor communication.\n"
            "3. Ignore sensitive information such as order ID, date, or phone number.\n"
            "4. Formulate a professional, empathetic response acknowledging the issue "
            "and assuring corrective action.\n"
            "5. Avoid direct actions like callbacks or refunds; keep it general and compliant."
        ),
        "output": {
            "customer_response": (
                "We’re very sorry to hear your order arrived damaged and that you had trouble reaching us."
                "We completely understand your frustration and appreciate you bringing this to our attention."
                "Our team is looking into the issue to ensure it’s addressed."
            )
        },
    },
    {
        "input": {
            "sentiment": "positive",
            "key_issues_praise": ["fast brewing", "quiet operation", "perfect coffee"],
            "summary": "Customer loves the new coffee maker for being fast, quiet, and effective.",
            "review_text": (
                "Absolutely love the new coffee maker! It's fast, quiet, and makes the "
                "perfect cup every time. Thanks, <PERSON>!"
            ),
        },
        "COT": (
            "1. Identify sentiment as positive.\n"
            "2. Highlight the praised aspects: fast brewing, quiet, great coffee.\n"
            "3. Construct a warm thank-you message acknowledging these aspects.\n"
            "4. Keep tone upbeat, friendly, and brand-consistent."
        ),
        "output": {
            "customer_response": (
                "We’re delighted to hear that you’re enjoying your new coffee maker! "
                "It’s great to know it’s fast, quiet, and makes your perfect cup every time. "
                "Thank you for being a valued customer!"
            )
        },
    },
    {
        "input": {
            "sentiment": "positive",
            "key_issues_praise": ["great service"],
            "summary": "Customer praised the service but asked for a coupon.",
            "review_text": (
                "Five stars! This is the best service I've ever received. "
                "<PERSON_2> (<EMAIL_ADDRESS>) you have a customer for life! "
                "Would love a coupon for my next purchase."
            ),
        },
        "COT": (
            "1. Identify sentiment as positive.\n"
            "2. Detect an actionable request (coupon) — this must be ignored per policy.\n"
            "3. Focus on gratitude and appreciation.\n"
            "4. Do not include any offers, PII, or internal instructions in the response."
        ),
        "output": {
            "customer_response": (
                "We’re thrilled that you had such a great experience with our service! "
                "Thank you for being a loyal customer — we truly appreciate your support."
            )
        },
    },
]


def generate_response(
    analyzed_review: Dict[str, Any], lang: str, mode: str = "safe"
) -> Dict[str, Any]:
    """
    Generate a customer response based on analyzed review data.

    Args:
        analyzed_review (dict): Analyzed review with keys 'sentiment',
            'key_issues_praise', 'summary', 'sanitized_review', and optional 'critical_ref'.

    Returns:
        dict: Contains 'customer_response' string and optional 'critical_ref'.
    """
    sentiment = analyzed_review["analysis"]["sentiment"]
    key_issues = analyzed_review["analysis"]["key_issues_praise"]
    summary = analyzed_review["analysis"]["summary"]
    safe_text = analyzed_review["sanitized_review"]
    critical_ref = analyzed_review.get("critical_ref")

    if mode.lower() == "unsafe":
        system_content = (
            "You are a helpful assistant that generates empathetic, professional responses."
            "Use only the information explicitly provided in the customer review — do not add, assume, or infer any details not stated. "
            "Use the reasoning style shown in the few-shot examples."
            f"{few_shot_examples}\n\n"
            f"The following customer review is written in language: {lang}. Please respond empathetically in the SAME LANGUAGE ({lang}"
            "Do not output reasoning steps; only return the final JSON response.\n\n"
            "Now analyze the following new input and respond accordingly. "
            "Always respond in JSON with key: customer_response."
        )

        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=f"Review Text: {safe_text}"),
        ]
        llm = ChatOpenAI()
        response = llm.invoke(messages)
        try:
            output = json.loads(response.content.strip())
        except Exception:
            output = {"customer_response": response.content.strip()}
        return output

    # Step 1: Prepare system prompt
    system_content = (
        "You are a helpful assistant that generates empathetic, professional, "
        "and policy-compliant customer responses." 
        "Use only the information explicitly provided in the customer review — do not add, assume, or infer any details not stated. "
        Use the reasoning style shown in the few-shot examples."
        f"{few_shot_examples}\n\n"
        f"The following customer review is written in {lang}. Please respond empathetically in the SAME LANGUAGE ({lang}"
        "Do not output reasoning steps; only return the final JSON response.\n\n"
        "Now analyze the following new input and respond accordingly. "
        "Always respond in JSON with key: customer_response."
    )

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(
            content=(
                f"Review Text: {safe_text}"
                f"Sentiment: {sentiment}\n"
                f"Key Issues/Praise: {key_issues}\n"
                f"Summary: {summary}\n"
            )
        ),
    ]

    # Step 2: Run LLM
    llm = ChatOpenAI()
    response = llm.invoke(messages)
    output = json.loads(response.content.strip())

    # Step 3: Append critical reference if present
    if critical_ref:
        output["customer_response"] += f" {critical_ref}"
        output["critical_ref"] = critical_ref

    return output
