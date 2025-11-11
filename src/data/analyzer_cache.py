"""Build and initialize a Presidio AnalyzerEngine with UK-specific recognizers."""

from presidio_analyzer import (
    AnalyzerEngine,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
)


def build_analyzer() -> AnalyzerEngine:
    """
    Initialize and return a Presidio AnalyzerEngine with custom UK recognizers.

    The analyzer includes:
        - UK-specific address recognizer (street names and postcodes)
        - UK phone number recognizer
        - Custom order ID recognizer
    """
    registry: RecognizerRegistry = RecognizerRegistry()
    registry.load_predefined_recognizers()

    # --- UK Postcode pattern ---
    uk_postcode_pattern = Pattern(
        name="uk_postcode_pattern",
        regex=r"\b([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})\b",
        score=1.0,
    )

    # --- UK Street pattern ---
    uk_street_pattern = Pattern(
        name="uk_street_pattern",
        regex=(
            r"\b\d{1,4}\s+[A-Za-z0-9'\-]+\s+"
            r"(Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Court|Ct|"
            r"Place|Pl|Close|Cl|Way|Gardens|Gdns)\b"
        ),
        score=0.8,
    )

    uk_address_recognizer = PatternRecognizer(
        supported_entity="ADDRESS",
        patterns=[uk_street_pattern, uk_postcode_pattern],
        context=["street", "road", "postcode", "flat", "building", "house", "address"],
    )

    # --- UK Phone number pattern ---
    phone_num_pattern = Pattern(
        name="phone_number_pattern",
        regex=r"(?:(?:\+44)|0)7\d{3}\s?\d{6}",
        score=1.0,
    )

    phone_num_recognizer = PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=[phone_num_pattern],
    )

    # --- Custom Order ID pattern ---
    order_id_pattern = Pattern(
        name="order_id_pattern",
        regex=r"\b[A-Z]{3}-\d{3}\b",
        score=1.0,
    )

    order_id_recognizer = PatternRecognizer(
        supported_entity="ORDER_ID",
        patterns=[order_id_pattern],
    )

    # --- Create analyzer and add custom recognizers ---
    analyzer = AnalyzerEngine(registry=registry, supported_languages=["en"])
    analyzer.registry.add_recognizer(uk_address_recognizer)
    analyzer.registry.add_recognizer(phone_num_recognizer)
    analyzer.registry.add_recognizer(order_id_recognizer)

    return analyzer


# Initialize once (shared instance)
ANALYZER: AnalyzerEngine = build_analyzer()
