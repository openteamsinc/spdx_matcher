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
