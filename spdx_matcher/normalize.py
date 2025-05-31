import re
from .word_variants import equivalent


def punctuation_replacer(text: str) -> str:
    """Handle punctuation variations per SPDX guidelines.

    Per SPDX guidelines:
    - Punctuation should be matched unless otherwise stated
    - Hyphens, dashes, en dash, em dash should be considered equivalent
    - Any variation of quotations should be considered equivalent
    """
    # Replace various dash types with pattern that matches any dash
    text = re.sub(r"[-–—−]", r"-", text)

    # Replace various quote types with pattern that matches any quote
    text = re.sub(r'["\'`]+', '"', text)

    return text


def copyright_symbol_replacer(text: str) -> str:
    """Handle copyright symbol variations.

    Per SPDX guidelines: "©", "(c)", or "Copyright" should be considered
    equivalent and interchangeable.
    """
    return re.sub(r"(©|\(c\)|copyright)", "copyright", text)


def http_protocol_replacer(text: str) -> str:
    """Handle HTTP/HTTPS protocol equivalence.

    Per SPDX guidelines: http:// and https:// should be considered equivalent.
    """
    return text.replace(r"http://", r"https://")


def bullet_replacer(text: str) -> str:
    """Return regex pattern that matches various bullet point styles.

    Per SPDX guidelines: Where a line starts with a bullet, number, letter,
    or some form of a list item (determined where list item is followed by
    a space, then the text of the sentence), ignore the list item for
    matching purposes.

    Matches:
    - Numbers: 1, 2., 1.0, etc.
    - Letters:  b., A), etc.
    - Symbols: -, *, •, etc.
    - Parenthetical: (1), (a), [i], etc.

    Returns:
        Regex pattern string that matches bullet point indicators
    """

    def _bullet_replacer_line(line):
        return re.sub(
            r"^\s*([0-9]+(\.[0-9])?|[\-*•]+|[abcdefgivx]+[\.\)]|\([abcdefgivx]+\)|\[[abcdefgivx]+\])\s+",
            " • ",
            line,
            flags=re.IGNORECASE,
        )

    return "\n".join(_bullet_replacer_line(line) for line in text.splitlines())


def whitespace_replacer(text: str) -> str:
    paragraphs = re.split(r"\n\s*\n+", text)
    # Clean whitespace within each paragraph
    cleaned = [re.sub(r"\s+", " ", p.strip()) for p in paragraphs if p.strip()]
    return "\n".join(cleaned)


def equivalent_replacer(text: str) -> str:
    """Replace equivalent words/phrases per SPDX guidelines.

    Per SPDX guidelines: Some words are considered equivalent and should be
    replaced with a standard form for matching purposes.
    """
    for new, old in equivalent:
        text = text.replace(old, new)
    return text


def normalize(text: str) -> str:
    """
    Normalize text for license matching.

    Args:
        text: The text to normalize

    Returns:
        Normalized text: lowercase, single spaces, no newlines
    """
    # Convert to lowercase
    text = text.lower()

    # Replace all whitespace (including newlines) with single spaces

    # Strip leading/trailing whitespace

    text = punctuation_replacer(text)
    text = bullet_replacer(text)
    text = copyright_symbol_replacer(text)
    text = http_protocol_replacer(text)
    text = equivalent_replacer(text)
    text = whitespace_replacer(text)
    text = text.strip()
    return text
