import pytest
import logging
from .matcher import match
from .types import LicenseMatcher, Matcher


def test_simple_license_match():
    """Test a simple license match with title, copyright, and parts."""

    # Create a simple LicenseMatcher
    license_matcher = LicenseMatcher(
        title="MIT License",
        copyright="Copyright[^\n]*",
        parts=["Permission is hereby granted", "THE SOFTWARE IS PROVIDED"],
        xpath="/test",
    )

    # License text that should match
    license_text = """MIT License

Copyright (c) 2023 Test Author

Permission is hereby granted, free of charge, to any person...

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY...

Some additional text that should remain unmatched.
"""

    # Test the match
    result = match(license_matcher, license_text)

    # Should return remaining text, not None
    assert result is not None
    assert "Some additional text" in result


def test_failed_match():
    """Test a license match that should fail."""

    license_matcher = LicenseMatcher(
        title="MIT License", copyright="^Copyright.*", parts=["This text is not in the license"], xpath="/test"
    )

    license_text = """MIT License

Copyright (c) 2023 Test Author

Permission is hereby granted...
"""

    # Test the match - should fail
    result = match(license_matcher, license_text)

    # Should return None because the part doesn't match
    assert result is None


def test_perfect_match():
    """Test a perfect match with no remaining text."""

    license_matcher = LicenseMatcher(
        title="MIT License", copyright=None, parts=["Permission is hereby granted"], xpath="/test"  # No copyright check
    )

    license_text = "MIT License\n\nPermission is hereby granted"

    result = match(license_matcher, license_text)

    # Should return empty or whitespace-only string
    assert result is not None
    assert result.strip() == ""
