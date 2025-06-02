import pytest
from spdx_license_matcher.normalize import unbox


@pytest.mark.parametrize(
    "text,expected,test_id",
    [
        # Basic box format
        (
            """***********
* Hello   *
* World   *
***********""",
            "***********\nHello\nWorld\n***********",
            "basic_box",
        ),
        # No box format
        ("Hello World\nThis is normal text", "Hello World\nThis is normal text", "no_box"),
        # Partial box format
        (
            """Normal line
* Boxed line   *
Another normal line
* Another boxed *""",
            "Normal line\nBoxed line\nAnother normal line\nAnother boxed",
            "partial_box",
        ),
        # Empty string
        ("", "", "empty_string"),
        # Single line
        ("* Hello World *", "Hello World", "single_line"),
        # Multiple asterisks
        ("*** Hello World ***", "Hello World", "multiple_asterisks"),
        # Leading/trailing spaces
        (
            "   * Hello *   \n** World **  ",
            "Hello\nWorld",
            "leading_trailing_spaces",
        ),
        # Only asterisks (box borders)
        (
            """*********
* Content *
*********""",
            "*********\nContent\n*********",
            "only_asterisks",
        ),
        # Mixed content
        (
            """License Agreement
*******************
* This software   *
* is licensed     *
*******************
End of license""",
            "License Agreement\n*******************\nThis software\nis licensed\n*******************\nEnd of license",
            "mixed_content",
        ),
        # Malformed box
        (
            """* Only start asterisk
End asterisk only *
* Both asterisks *
* Missing end
""",
            "* Only start asterisk\nEnd asterisk only *\nBoth asterisks\n* Missing end",
            "malformed_box",
        ),
        # Whitespace only content
        ("*    *", "", "whitespace_only_content"),
        # Preserves internal asterisks
        ("* Hello * World *", "Hello * World", "preserves_internal_asterisks"),
    ],
)
def test_unbox(text, expected, test_id):
    """Test unbox function with various input patterns."""
    result = unbox(text)
    assert result == expected
