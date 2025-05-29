import re


def normalize(text: str) -> str:
    """
    Normalize text for license matching.

    Args:
        text: The text to normalize

    Returns:
        Normalized text: lowercase, single spaces, no newlines
    """
    # Convert to lowercase
    normalized = text.lower()

    # Replace all whitespace (including newlines) with single spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Strip leading/trailing whitespace
    normalized = normalized.strip()

    return normalized
