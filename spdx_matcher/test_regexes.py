"""
Tests for SPDX License List matching guideline replacer functions.
"""

import pytest
import re
from .regexes import (
    whitespace_replacer,
    punctuation_replacer,
    varietal_spelling_replacer,
    copyright_symbol_replacer,
    http_protocol_replacer,
    bullet_replacer,
    apply_all_replacers,
)


class TestWhitespaceReplacer:
    """Test whitespace normalization per SPDX guidelines."""

    @pytest.mark.parametrize(
        "input_text,expected_to_match",
        [
            ("word1 word2", "word1 word2"),
            ("word1 word2", "word1  word2"),
            ("word1     word2", "word1\tword2"),
            ("word1\n\nword2", "word1\nword2"),
            ("word1 word2", "word1\r\nword2"),
            ("word1\t\t\tword2", "word1   \t\n  word2"),
        ],
    )
    def test_single_space_replacement(self, input_text, expected_to_match):
        result = whitespace_replacer(input_text)
        print("result", repr(result))
        match = re.match(result, expected_to_match)
        assert match is not None


class TestPunctuationReplacer:
    """Test punctuation handling per SPDX guidelines."""

    @pytest.mark.parametrize(
        "input_text,expected_to_match",
        [
            ("word-word", "word-word"),
            ("word-word", "word–word"),  # en dash
            ("word-word", "word—word"),  # em dash
            ("word-word", "word−word"),  # minus sign
            ('"quoted text"', '"quoted text`'),
            ('"quoted text"', "'quoted text'"),
            ('"quoted text"', '"quoted text"'),
            ('"quoted text"', "'quoted text'"),
            ('"quoted text"', "`quoted text`"),
        ],
    )
    def test_punctuation_replacement(self, input_text, expected_to_match):
        result = punctuation_replacer(input_text)
        print(repr(result), repr(expected_to_match))
        match = re.match(result, expected_to_match)
        assert match is not None


class TestVarietalSpellingReplacer:
    """Test varietal spelling handling per SPDX guidelines."""

    @pytest.mark.parametrize(
        "input_text,expected_to_match",
        [
            ("license", "license"),
            ("license", "licence"),
            ("acknowledgment", "acknowledgment"),
            ("acknowledgment", "acknowledgement"),
            ("organization", "organization"),
            ("organization", "organisation"),
            ("analyze", "analyze"),
            ("analyze", "analyse"),
            ("noncommercial", "non-commercial"),
            ("non-commercial", "noncommercial"),
            ("while", "whilst"),
            ("whilst", "while"),
            ("fulfill", "fulfil"),
            ("fulfil", "fulfill"),
            ("program", "programme"),
            ("programme", "program"),
        ],
    )
    def test_spelling_variations(self, input_text, expected_to_match):
        result = varietal_spelling_replacer(input_text)
        match = re.search(result, expected_to_match)
        assert match is not None, f"Expected regex:{result!r} to match {expected_to_match!r} for input {input_text!r}"


class TestCopyrightSymbolReplacer:
    """Test copyright symbol handling per SPDX guidelines."""

    @pytest.mark.parametrize(
        "input_text,expected_to_match",
        [
            ("©", "©"),
            ("©", "(c)"),
            ("©", "Copyright"),
            ("©", "copyright"),
            ("(c)", "©"),
            ("(c)", "(c)"),
            ("(c)", "copyright"),
            ("Copyright", "©"),
            ("Copyright", "Copyright"),
            ("© 2023 Example Corp", "Copyright 2023 Example Corp"),
            ("(c) 2023 Example Corp", "© 2023 Example Corp"),
            ("Copyright 2023 Example", "(c) 2023 Example"),
            ("Some text © symbol here", "Some text (c) symbol here"),
            ("Mixed Copyright and © symbols", "Mixed (c) and copyright symbols"),
        ],
    )
    def test_copyright_symbol_equivalence(self, input_text, expected_to_match):
        result = copyright_symbol_replacer(input_text)
        match = re.search(result, expected_to_match, re.IGNORECASE | re.DOTALL)
        assert match is not None, f"Expected regex:{result!r} to match {expected_to_match!r} for input {input_text!r}"


class TestHttpProtocolReplacer:
    """Test HTTP/HTTPS protocol handling per SPDX guidelines."""

    @pytest.mark.parametrize(
        "input_text,expected_to_match",
        [
            ("http://example.com", "http://example.com"),
            ("http://example.com", "https://example.com"),
            ("https://example.com", "http://example.com"),
            ("https://example.com", "https://example.com"),
            ("Visit http://opensource.org for details", "Visit https://opensource.org for details"),
            ("See https://www.apache.org/licenses/", "See http://www.apache.org/licenses/"),
            ("Multiple http://site1.com and https://site2.com", "Multiple https://site1.com and http://site2.com"),
        ],
    )
    def test_http_https_equivalence(self, input_text, expected_to_match):
        result = http_protocol_replacer(input_text)
        match = re.search(result, expected_to_match)
        assert match is not None, f"Expected regex:{result!r} to match {expected_to_match!r} for input {input_text!r}"


class TestBulletReplacer:
    """Test bullet point pattern matching per SPDX guidelines."""

    @pytest.mark.parametrize(
        "bullet_text",
        [
            "2) ",
            "2: ",
            "2. ",
            "10. ",
            "b. ",
            "A) ",
            "Z. ",
            "- ",
            "* ",
            "• ",
            "(1) ",
            "(a) ",
            "(A) ",
            "(10) ",
            "[1] ",
            "[a] ",
            "[A] ",
            "[i] ",
            "[10] ",
        ],
    )
    def test_bullet_pattern_matches(self, bullet_text):
        pattern = bullet_replacer()
        match = re.match(pattern, bullet_text)
        assert match is not None, f"Expected pattern {pattern!r} to match bullet text {bullet_text!r}"

    def test_bullet_pattern_with_text(self):
        """Test that bullet pattern matches at start of lines with following text."""
        pattern = bullet_replacer()
        test_cases = [
            "1. This is item one",
            "a) This is item a",
            "* Bullet point here",
            "- Another bullet",
            "(1) Numbered in parens",
            "[i] Roman numeral in brackets",
        ]

        for text in test_cases:
            match = re.match(pattern, text)
            assert match is not None, f"Expected pattern {pattern!r} to match start of {text!r}"

    def test_non_bullet_text_doesnt_match(self):
        """Test that non-bullet text doesn't match the bullet pattern."""
        pattern = bullet_replacer()
        non_bullet_cases = [
            "This is regular text",
            "No bullet here",
            "123 not a bullet",
            "abc not a bullet",
            "Just some words",
        ]

        for text in non_bullet_cases:
            match = re.match(pattern, text)
            assert match is None, f"Expected pattern {pattern!r} NOT to match {text!r}"

    def test_all_replacers_1(self):
        r = """
        (the
         b
        """
        replaced = apply_all_replacers(r)

        print(replaced)
        assert replaced == r"\s+\(the\s+b\s+"
