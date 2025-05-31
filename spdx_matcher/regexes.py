"""
SPDX License List matching guideline replacer functions.

These functions implement the SPDX License List Matching Guidelines to convert
license text into matchable regular expressions by applying various normalization
rules for whitespace, capitalization, punctuation, and other variations.
"""

import re
from .word_variants import word_variants


def whitespace_replacer(text: str) -> str:
    """Replace all whitespace with a single space pattern.

    Per SPDX guidelines: All whitespace should be treated as a single blank space.
    """
    # Handle both regular whitespace and escaped whitespace from re.escape()
    # First replace any sequence of escaped spaces and regular whitespace with \\s+

    # can not use \s in repl arg of re.sub
    text = re.sub(r"(\\\\ |\\\s|\s)+", r"\\s+", text)

    return text


def punctuation_replacer(text: str) -> str:
    """Handle punctuation variations per SPDX guidelines.

    Per SPDX guidelines:
    - Punctuation should be matched unless otherwise stated
    - Hyphens, dashes, en dash, em dash should be considered equivalent
    - Any variation of quotations should be considered equivalent
    """
    # Replace various dash types with pattern that matches any dash
    text = re.sub(r"[-–—−]", r"[-–—−]", text)

    # Replace various quote types with pattern that matches any quote
    text = re.sub(r'[""' '"`]', r'[\'"`]', text)

    return text


def x_code_comment_replacer(text: str) -> str:
    """Remove code comment indicators and separators.

    Per SPDX guidelines:
    - Ignore code comment indicators at the beginning of each line
    - Ignore repeated non-letter characters (3+) used for visual separation
    """
    lines = text.split("\n")
    processed_lines = []

    for line in lines:
        # Remove comment indicators at start of line
        line = re.sub(r"^[\s*/#-]*", "", line)

        # Remove visual separators (3+ repeated non-letter chars)
        line = re.sub(r"[^a-zA-Z]{3,}", "", line)

        processed_lines.append(line)

    return "\n".join(processed_lines)


def varietal_spelling_replacer(text: str) -> str:
    """Handle varietal word spellings.

    Per SPDX guidelines: Use equivalent words list for spelling variations.
    Common variations in licenses include:
    - license/licence
    - acknowledgment/acknowledgement
    - organization/organisation
    """

    for original, pattern in word_variants.items():
        text = re.sub(f"\\b{original}\\b", pattern, text, flags=re.IGNORECASE)

    return text


def copyright_symbol_replacer(text: str) -> str:
    """Handle copyright symbol variations.

    Per SPDX guidelines: "©", "(c)", or "Copyright" should be considered
    equivalent and interchangeable.
    """
    return re.sub(r"(©|\(c\)|copyright)", r"(©|\\(c\\)|copyright)", text, flags=re.IGNORECASE)


def http_protocol_replacer(text: str) -> str:
    """Handle HTTP/HTTPS protocol equivalence.

    Per SPDX guidelines: http:// and https:// should be considered equivalent.
    """
    return re.sub(r"https?://", r"https?://", text)


def bullet_replacer() -> str:
    """Return regex pattern that matches various bullet point styles.

    Per SPDX guidelines: Where a line starts with a bullet, number, letter,
    or some form of a list item (determined where list item is followed by
    a space, then the text of the sentence), ignore the list item for
    matching purposes.

    Matches:
    - Numbers: 1, 2., 1.0, etc.
    - Letters: a, b., A), etc.
    - Symbols: -, *, •, etc.
    - Parenthetical: (1), (a), [i], etc.

    Returns:
        Regex pattern string that matches bullet point indicators
    """
    return r"([a-zA-Z0-9]+[:\.\)]|[•\-\*]|\([a-zA-Z0-9]+\)|\[[a-zA-Z0-9]+\])\s+"


def apply_all_replacers(text: str) -> str:
    """Apply all SPDX matching guideline replacers to text.

    Args:
        text: Original license text

    Returns:
        Text processed with all SPDX matching guidelines applied
    """

    # First escape regex special characters to treat text as literal
    text = re.escape(text)

    # Order matters for some replacers
    text = copyright_symbol_replacer(text)
    text = http_protocol_replacer(text)
    text = varietal_spelling_replacer(text)
    text = punctuation_replacer(text)
    text = whitespace_replacer(text)

    return text
