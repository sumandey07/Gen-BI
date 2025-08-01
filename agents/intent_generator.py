import re
from intent_config import PATTERN_CONFIG
#TODO- As of now, a hardcode version is implemented to fetch entities and identify intent,
# Going forward given the required insfrastructure, we will be using a fine tuned large LLM capable of handling similarity and semantic search and either autonomously find the intent or with liitle bit of pattern match

def extract_intent(user_input: str) -> str:
    """
    Extract labelled key‑value pairs or metric names from the user query.
    Returns only values that match patterns explicitly in the input.
    """
    intent_parts = []

    for config in PATTERN_CONFIG.values():
        match = _first_match(user_input, config["patterns"])
        if match:
            intent_parts.append(_format_piece(match, config))

    return (
        " and ".join(intent_parts)
        if intent_parts
        else "General query or intent not identified."
    )


def _first_match(text: str, patterns: list[str]) -> str:
    """Return the first regex capture group that matches, or non-capturing match for metrics."""
    for pat in patterns:
        matches = re.findall(pat, text, flags=re.IGNORECASE)
        if matches:
            if isinstance(matches[0], tuple):
                return matches[0][0].strip()
            return matches[0].strip() if isinstance(matches[0], str) else ""
    return ""


def _format_piece(value: str, config: dict) -> str:
    """
    Formats the extracted value using the label from config,
    adds quotes except for numeric version strings, and applies metric logic.
    """
    label = config.get("label", "Unknown")

    if config.get("is_metric", False):
        return f"{label}: {config.get('metric_name', 'metric')}"

    if config.get("quote", True):
        return f"{label}: '{value}'"
    return f"{label}: {value}"
