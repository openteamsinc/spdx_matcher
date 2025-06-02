import re
from .word_variants import equivalent


def punctuation_normalizer(text: str) -> str:
    """
    handle commas that are,like,this
    """

    text = re.sub(r"([a-zA-Z0-9'])\s*([\.,:])", r"\1\2", text)  # Ensure no space before puncuation
    text = re.sub(r"([,:])([a-zA-Z0-9'])", r"\1 \2", text)  # Ensure space after puncuation

    text = re.sub(r"\s*([,])\s*", r"\1 ", text)  # Normalize spaces around commas
    return text


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
    # text = re.sub(r'["\'`’“”]+', "'", text)
    text = re.sub(r'["\'`’“”‘„]+', "'", text)

    return text


def copyright_symbol_replacer(text: str) -> str:
    """Handle copyright symbol variations.

    Per SPDX guidelines: "©", "(c)", or "Copyright" should be considered
    equivalent and interchangeable.
    """
    text0 = re.sub(r"(copyright\s*©|copyright\s*\(c\)|copyright)", "copyright", text)
    # if text != text0:
    #     print("Changed >>", (text,))
    #     print("        <<", (text0,))
    return text0


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
            r"^\s*([0-9]+(\.[0-9])?|[\.\-*•]+|[abcdefgivx]+[\.\)]|\([abcdefgivx]+\)|\[[abcdefgivx]+\])\s+",
            " • ",
            line,
            flags=re.IGNORECASE,
        )

    return "\n".join(_bullet_replacer_line(line) for line in text.splitlines())


def separator_replacer(text: str) -> str:
    """
    To avoid the possibility of a non-match due to the existence or absence of code
    comment indicators placed within the license text, e.g., at the start of
    each line of text, or repetitive characters to establish a separation of text,
    e.g., ---, ===, ___, or ***.

    Guideline:
        A non-letter character repeated 3 or more times to establish a visual separation
        should be ignored for matching purposes.
    """
    # return text

    def _separator_replacer_line(line):
        # Replace any sequence of non-letter characters repeated 3 or more times with a single space
        return re.sub(r"^([^a-zA-Z0-9\s])\1{3,}", " ", line).strip()

    return "\n".join(_separator_replacer_line(line) for line in text.splitlines())


def unbox(text: str) -> str:
    """Remove text boxing characters.
    eg
    ***********
    * Hello   *
    * World   *
    ***********
    """

    def _unbox_line(line: str) -> str:
        # Remove leading and trailing asterisks and spaces
        return re.sub(r"^\s*\*+\s+(.*)\s+\*+\s*$", r"\1", line).strip()

    return "\n".join(_unbox_line(line) for line in text.splitlines())


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


def normalize(text: str, bullets=False) -> str:
    """
    Normalize text for license matching.

    Args:
        text: The text to normalize

    Returns:
        Normalized text: lowercase, single spaces, no newlines
    """

    text = text.lower()

    text = unbox(text)
    text = punctuation_replacer(text)
    text = punctuation_normalizer(text)
    text = separator_replacer(text)

    if bullets:
        text = bullet_replacer(text)

    text = copyright_symbol_replacer(text)
    text = http_protocol_replacer(text)
    text = whitespace_replacer(text)
    text = equivalent_replacer(text)
    text = text.strip()
    return text
