import xml.etree.ElementTree as ET
from spdx_matcher.matcher import match_p, match_title_text, match_copyright, match_list, match_list_item, normalize


def test_match_p_simple():
    """Test match_p with simple paragraph element."""
    # Create a simple paragraph element
    xml_string = """<p xmlns="http://www.spdx.org/license">Permission is granted to use this software.</p>"""
    p_elem = ET.fromstring(xml_string)

    test_text = """
    Permission is granted to use this software.
    Some extra text here.
    """

    result = match_p(p_elem, test_text)
    
    # Should have the matched text removed
    assert result is not None
    assert "some extra text here" in result.lower()
    assert "permission is granted" not in result.lower()


def test_match_p_no_match():
    """Test match_p when no match is found."""
    xml_string = """<p xmlns="http://www.spdx.org/license">This text will not match.</p>"""
    p_elem = ET.fromstring(xml_string)

    test_text = """
    Permission is granted to use this software.
    Some extra text here.
    """

    result = match_p(p_elem, test_text)
    
    # Should return None when no match
    assert result is None


def test_match_p_with_alt():
    """Test match_p with alt element."""
    xml_string = """<p xmlns="http://www.spdx.org/license">Permission is granted to use this <alt match="software|code">software</alt>.</p>"""
    p_elem = ET.fromstring(xml_string)

    test_text = """
    Permission is granted to use this code.
    Some extra text here.
    """

    result = match_p(p_elem, test_text)

    # Should have the matched text removed
    assert result is not None
    assert "some extra text here" in result.lower()
    assert "permission is granted" not in result.lower()


def test_match_p_with_optional():
    """Test match_p with optional element."""
    xml_string = """<p xmlns="http://www.spdx.org/license">The above copyright notice<optional> and this permission notice</optional> shall be included.</p>"""
    p_elem = ET.fromstring(xml_string)

    # Test with optional text present
    test_text1 = """
    The above copyright notice and this permission notice shall be included.
    Some extra text here.
    """

    result1 = match_p(p_elem, test_text1)
    assert result1 is not None
    assert "some extra text here" in result1.lower()

    # Test with optional text missing
    test_text2 = """
    The above copyright notice shall be included.
    Some extra text here.
    """

    result2 = match_p(p_elem, test_text2)
    assert result2 is not None
    assert "some extra text here" in result2.lower()


def test_match_title_text_simple():
    """Test match_title_text with simple title."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """MIT License

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)

    # Should have the title line removed
    assert "mit license" not in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_title_text_with_prefix():
    """Test match_title_text with prefix text."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """Beautiful Soup is made available under the MIT license:

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)

    # Should have the line with prefix removed
    assert "beautiful soup" not in result.lower()
    assert "mit license" not in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_title_text_with_suffix():
    """Test match_title_text with suffix text."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """This project uses the MIT License (see below)

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should have the line with suffix removed
    assert "mit license" not in result.lower()
    assert "see below" not in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_title_text_no_match():
    """Test match_title_text when title is not found."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>Apache License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """MIT License

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should return original text unchanged
    assert result == test_text
    assert "mit license" in result.lower()


def test_match_title_text_empty_element():
    """Test match_title_text with empty titleText element."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """MIT License

Permission is hereby granted, free of charge.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should return original text unchanged
    assert result == test_text


def test_match_title_text_markdown_h1():
    """Test match_title_text with Markdown H1 style."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """# MIT License

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should have the markdown title line removed
    assert "mit license" not in result.lower()
    assert "#" not in result
    assert "permission is hereby granted" in result.lower()


def test_match_title_text_markdown_h2():
    """Test match_title_text with Markdown H2 style."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """## MIT License

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should have the markdown title line removed
    assert "mit license" not in result.lower()
    assert "##" not in result
    assert "permission is hereby granted" in result.lower()


def test_match_title_text_rst_with_underline():
    """Test match_title_text with RST style underline."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """MIT License
===========

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should have the title line removed but underline might remain
    assert "mit license" not in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_title_text_rst_with_overline():
    """Test match_title_text with RST style overline and underline."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """===========
MIT License
===========

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should have the title line removed but decoration might remain
    assert "mit license" not in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_title_text_markdown_with_bold():
    """Test match_title_text with Markdown bold formatting."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """**MIT License**

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should have the title line removed
    assert "mit license" not in result.lower()
    assert "**" not in result
    assert "permission is hereby granted" in result.lower()


def test_match_title_text_mixed_formatting():
    """Test match_title_text with mixed prefix and markdown formatting."""
    xml_string = """<titleText xmlns="http://www.spdx.org/license">
        <p>MIT License</p>
    </titleText>"""
    title_elem = ET.fromstring(xml_string)

    test_text = """This software is licensed under the **MIT License** terms:

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""

    result = match_title_text(title_elem, test_text)
    print(f"Result: {repr(result)}")

    # Should have the line with mixed formatting removed
    assert "mit license" not in result.lower()
    assert "this software is licensed" not in result.lower()
    assert "**" not in result
    assert "permission is hereby granted" in result.lower()


def test_match_copyright_simple():
    """Test match_copyright with simple copyright."""
    xml_string = """<copyrightText xmlns="http://www.spdx.org/license">
        <p>Copyright (c) &lt;year&gt; &lt;copyright holders&gt;</p>
    </copyrightText>"""
    copyright_elem = ET.fromstring(xml_string)
    
    test_text = """Copyright (c) 2023 John Doe

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""
    
    result = match_copyright(copyright_elem, test_text)
    
    # Should have the copyright line removed
    assert "copyright" not in result.lower()
    assert "john doe" not in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_copyright_multiple_lines():
    """Test match_copyright with multiple copyright lines."""
    xml_string = """<copyrightText xmlns="http://www.spdx.org/license">
        <p>Copyright (c) &lt;year&gt; &lt;copyright holders&gt;</p>
    </copyrightText>"""
    copyright_elem = ET.fromstring(xml_string)
    
    test_text = """Copyright (c) 2023 John Doe
Copyright (c) 2024 Jane Smith
All rights reserved.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""
    
    result = match_copyright(copyright_elem, test_text)
    
    # Should have all copyright lines removed
    assert "copyright" not in result.lower()
    assert "john doe" not in result.lower()
    assert "jane smith" not in result.lower()
    assert "all rights reserved" not in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_copyright_with_c_symbol():
    """Test match_copyright with (c) symbol."""
    xml_string = """<copyrightText xmlns="http://www.spdx.org/license">
        <p>Copyright (c) &lt;year&gt; &lt;copyright holders&gt;</p>
    </copyrightText>"""
    copyright_elem = ET.fromstring(xml_string)
    
    test_text = """(c) 2023 Example Corp

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""
    
    result = match_copyright(copyright_elem, test_text)
    
    # Should have the copyright line removed
    assert "(c)" not in result
    assert "example corp" not in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_copyright_no_copyright():
    """Test match_copyright when no copyright is present."""
    xml_string = """<copyrightText xmlns="http://www.spdx.org/license">
        <p>Copyright (c) &lt;year&gt; &lt;copyright holders&gt;</p>
    </copyrightText>"""
    copyright_elem = ET.fromstring(xml_string)
    
    test_text = """MIT License

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files.
"""
    
    result = match_copyright(copyright_elem, test_text)
    
    # Should return original text unchanged
    assert result == test_text


def test_match_copyright_empty_element():
    """Test match_copyright with empty copyrightText element."""
    xml_string = """<copyrightText xmlns="http://www.spdx.org/license">
    </copyrightText>"""
    copyright_elem = ET.fromstring(xml_string)
    
    test_text = """Copyright (c) 2023 John Doe

Permission is hereby granted, free of charge.
"""
    
    result = match_copyright(copyright_elem, test_text)
    
    # Should return original text unchanged
    assert result == test_text


def test_match_copyright_preserves_license_text():
    """Test that match_copyright doesn't remove license text mentioning copyright."""
    xml_string = """<copyrightText xmlns="http://www.spdx.org/license">
        <p>Copyright (c) &lt;year&gt; &lt;copyright holders&gt;</p>
    </copyrightText>"""
    copyright_elem = ET.fromstring(xml_string)
    
    test_text = """Copyright (c) Leonard Richardson

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
"""
    
    result = match_copyright(copyright_elem, test_text)
    
    # Should remove the actual copyright line but preserve license text about copyright
    assert "leonard richardson" not in result.lower()
    assert "the above copyright notice and this permission notice shall be" in result.lower()
    assert "permission is hereby granted" in result.lower()


def test_match_copyright_sphinx_example():
    """Test match_copyright with sphinxcontrib-applehelp license example."""
    xml_string = """<copyrightText xmlns="http://www.spdx.org/license">
        <p>Copyright (c) &lt;year&gt; &lt;copyright holders&gt;</p>
    </copyrightText>"""
    copyright_elem = ET.fromstring(xml_string)
    
    test_text = """License for sphinxcontrib-applehelp
===================================

Copyright (c) 2007-2019 by the Sphinx team
(see https://github.com/sphinx-doc/sphinx/blob/master/AUTHORS).
All rights reserved.

Redistribution and use in source and binary forms, with or without
"""
    
    result = match_copyright(copyright_elem, test_text)
    
    # Should remove copyright lines but preserve title and license text
    assert "License for sphinxcontrib-applehelp" in result
    assert "===================================" in result
    assert "sphinx team" not in result.lower()
    assert "all rights reserved" not in result.lower()
    assert "Redistribution and use in source and binary forms" in result


def test_match_list_item_simple():
    """Test match_list_item with simple item."""
    xml_string = """<item xmlns="http://www.spdx.org/license">
        <bullet>1.</bullet>
        Redistributions of source code must retain the above copyright notice.
    </item>"""
    item_elem = ET.fromstring(xml_string)
    
    test_text = """1. Redistributions of source code must retain the above copyright notice.
2. Redistributions in binary form must reproduce the above copyright notice.
"""
    
    result = match_list_item(item_elem, test_text)
    
    # Should have the first item removed
    assert result is not None
    assert "1. Redistributions of source code" not in result
    assert "2. Redistributions in binary form" in result


def test_match_list_item_no_match():
    """Test match_list_item when no match is found."""
    xml_string = """<item xmlns="http://www.spdx.org/license">
        <bullet>1.</bullet>
        This text will not match.
    </item>"""
    item_elem = ET.fromstring(xml_string)
    
    test_text = """1. Redistributions of source code must retain the above copyright notice.
2. Redistributions in binary form must reproduce the above copyright notice.
"""
    
    result = match_list_item(item_elem, test_text)
    
    # Should return None when no match
    assert result is None


def test_match_list_bsd_style():
    """Test match_list with BSD-style list."""
    xml_string = """<list xmlns="http://www.spdx.org/license">
        <item>
            <bullet>1.</bullet>
            Redistributions of source code must retain the above copyright notice, this list of conditions
            and the following disclaimer.
        </item>
        <item>
            <bullet>2.</bullet>
            Redistributions in binary form must reproduce the above copyright notice, this list of conditions
            and the following disclaimer in the documentation and/or other materials provided with the
            distribution.
        </item>
    </list>"""
    list_elem = ET.fromstring(xml_string)
    
    test_text = """Redistribution and use in source and binary forms, with or without modification, are permitted provided
that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions
and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions
and the following disclaimer in the documentation and/or other materials provided with the
distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
"""
    
    result = match_list(list_elem, test_text)
    
    # Should have both list items removed
    assert result is not None
    assert "1. Redistributions of source code" not in result
    assert "2. Redistributions in binary form" not in result
    assert "THIS SOFTWARE IS PROVIDED" in result


def test_match_list_partial_failure():
    """Test match_list when one item fails to match."""
    xml_string = """<list xmlns="http://www.spdx.org/license">
        <item>
            <bullet>1.</bullet>
            Redistributions of source code must retain the above copyright notice.
        </item>
        <item>
            <bullet>2.</bullet>
            This text will not match.
        </item>
    </list>"""
    list_elem = ET.fromstring(xml_string)
    
    test_text = """1. Redistributions of source code must retain the above copyright notice.
2. Redistributions in binary form must reproduce the above copyright notice.
"""
    
    result = match_list(list_elem, test_text)
    
    # Should return None when any item fails to match
    assert result is None


def test_match_list_with_bullet_points():
    """Test match_list with bullet points instead of numbers - should fail."""
    xml_string = """<list xmlns="http://www.spdx.org/license">
        <item>
            <bullet>1.</bullet>
            Redistributions of source code must retain the above copyright notice, this list of conditions
            and the following disclaimer.
        </item>
        <item>
            <bullet>2.</bullet>
            Redistributions in binary form must reproduce the above copyright notice, this list of conditions
            and the following disclaimer in the documentation and/or other materials provided with the
            distribution.
        </item>
    </list>"""
    list_elem = ET.fromstring(xml_string)
    
    test_text = """Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright
  notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

"""
    
    result = match_list(list_elem, test_text)
    
    # This should fail because "1." doesn't match "*"
    assert result is None


def test_strip_matches_with_optional_elements():
    """Test strip_matches function with optional elements."""
    from spdx_matcher.strip_matches import strip_matches
    
    # Create a license XML with optional elements similar to OLFL-1.3.xml
    xml_string = """<SPDXLicenseCollection xmlns="http://www.spdx.org/license">
        <license licenseId="TEST-1.0" name="Test License">
            <text>
                <titleText>
                    <p>Test License</p>
                </titleText>
                <optional>
                    <p>TERMS AND CONDITIONS FOR USE</p>
                </optional>
                <p>Permission is hereby granted to use this software.</p>
                <optional>
                    <p>END OF TERMS AND CONDITIONS</p>
                </optional>
            </text>
        </license>
    </SPDXLicenseCollection>"""
    
    root = ET.fromstring(xml_string)
    
    # Test 1: License text with all optional elements present
    license_text_with_optional = """Test License

TERMS AND CONDITIONS FOR USE

Permission is hereby granted to use this software.

END OF TERMS AND CONDITIONS

Some remaining text here.
"""
    
    result1 = strip_matches(root, license_text_with_optional)
    assert result1 is not None
    assert "some remaining text here" in result1.lower()
    assert "test license" not in result1.lower()
    assert "terms and conditions" not in result1.lower()
    assert "permission is hereby granted" not in result1.lower()
    assert "end of terms" not in result1.lower()
    
    # Test 2: License text with some optional elements missing (should still pass)
    license_text_partial_optional = """Test License

Permission is hereby granted to use this software.

END OF TERMS AND CONDITIONS

Some remaining text here.
"""
    
    result2 = strip_matches(root, license_text_partial_optional)
    assert result2 is not None
    assert "some remaining text here" in result2.lower()
    assert "test license" not in result2.lower()
    assert "permission is hereby granted" not in result2.lower()
    assert "end of terms" not in result2.lower()
    
    # Test 3: License text with no optional elements (should still pass)
    license_text_no_optional = """Test License

Permission is hereby granted to use this software.

Some remaining text here.
"""
    
    result3 = strip_matches(root, license_text_no_optional)
    assert result3 is not None
    assert "some remaining text here" in result3.lower()
    assert "test license" not in result3.lower()
    assert "permission is hereby granted" not in result3.lower()
    
    # Test 4: License text missing required elements (should fail)
    license_text_missing_required = """Test License

TERMS AND CONDITIONS FOR USE

Some text that doesn't match the required paragraph.

END OF TERMS AND CONDITIONS
"""
    
    result4 = strip_matches(root, license_text_missing_required)
    assert result4 is None  # Should fail because required paragraph is missing


def test_strip_matches_optional_with_nested_elements():
    """Test strip_matches with optional elements containing lists."""
    from spdx_matcher.strip_matches import strip_matches
    
    # Create XML with optional element containing a list
    xml_string = """<SPDXLicenseCollection xmlns="http://www.spdx.org/license">
        <license licenseId="TEST-2.0" name="Test License with List">
            <text>
                <titleText>
                    <p>Test License with Lists</p>
                </titleText>
                <optional>
                    <list>
                        <item>
                            <bullet>1.</bullet>
                            First optional condition
                        </item>
                        <item>
                            <bullet>2.</bullet>
                            Second optional condition
                        </item>
                    </list>
                </optional>
                <p>The software is provided as-is.</p>
            </text>
        </license>
    </SPDXLicenseCollection>"""
    
    root = ET.fromstring(xml_string)
    
    # Test with optional list present
    license_text_with_list = """Test License with Lists

1. First optional condition
2. Second optional condition

The software is provided as-is.

Additional text.
"""
    
    result1 = strip_matches(root, license_text_with_list)
    assert result1 is not None
    assert "additional text" in result1.lower()
    assert "first optional condition" not in result1.lower()
    assert "second optional condition" not in result1.lower()
    assert "the software is provided as-is" not in result1.lower()
    
    # Test without optional list (should still pass)
    license_text_no_list = """Test License with Lists

The software is provided as-is.

Additional text.
"""
    
    result2 = strip_matches(root, license_text_no_list)
    assert result2 is not None
    assert "additional text" in result2.lower()
    assert "the software is provided as-is" not in result2.lower()


def test_strip_matches_with_implicit_text():
    """Test strip_matches with implicit text content (like mpi-permissive.xml)."""
    from spdx_matcher.strip_matches import strip_matches
    
    # Create XML similar to mpi-permissive.xml with implicit text content
    xml_string = """<SPDXLicenseCollection xmlns="http://www.spdx.org/license">
        <license licenseId="mpi-permissive" name="mpi Permissive License">
            <text>
                <copyrightText>
                    <p>Copyright (C) 2000-2004 by Etnus, LLC</p>
                </copyrightText>

  Permission is hereby granted to use, reproduce, prepare derivative
  works, and to redistribute to others.

					  DISCLAIMER

  Neither Etnus, nor any of their employees, makes any warranty
  express or implied, or assumes any legal liability or
  responsibility for the accuracy, completeness, or usefulness of any
  information, apparatus, product, or process disclosed, or
  represents that its use would not infringe privately owned rights.

  This code was written by
  James Cownie: Etnus, LLC.
            </text>
        </license>
    </SPDXLicenseCollection>"""
    
    root = ET.fromstring(xml_string)
    
    # Test license text that matches the implicit content
    license_text = """Copyright (C) 2000-2004 by Etnus, LLC

Permission is hereby granted to use, reproduce, prepare derivative
works, and to redistribute to others.

                      DISCLAIMER

Neither Etnus, nor any of their employees, makes any warranty
express or implied, or assumes any legal liability or
responsibility for the accuracy, completeness, or usefulness of any
information, apparatus, product, or process disclosed, or
represents that its use would not infringe privately owned rights.

This code was written by
James Cownie: Etnus, LLC.

Some additional remaining text.
"""
    
    result = strip_matches(root, license_text)
    assert result is not None
    assert "some additional remaining text" in result.lower()
    # All the license content should be removed
    assert "permission is hereby granted" not in result.lower()
    assert "disclaimer" not in result.lower()
    assert "etnus" not in result.lower()
    assert "james cownie" not in result.lower()


def test_strip_matches_with_mixed_implicit_and_explicit_elements():
    """Test strip_matches with both implicit text and explicit elements."""
    from spdx_matcher.strip_matches import strip_matches
    
    # Create XML with implicit text mixed with explicit elements
    xml_string = """<SPDXLicenseCollection xmlns="http://www.spdx.org/license">
        <license licenseId="MIXED-1.0" name="Mixed License">
            <text>
                <titleText>
                    <p>Mixed License</p>
                </titleText>

Some implicit license text here.

                <p>This is an explicit paragraph.</p>

More implicit text after the paragraph.

                <optional>
                    <p>Optional terms may apply.</p>
                </optional>

Final implicit text at the end.
            </text>
        </license>
    </SPDXLicenseCollection>"""
    
    root = ET.fromstring(xml_string)
    
    # Test with all content present
    license_text = """Mixed License

Some implicit license text here.

This is an explicit paragraph.

More implicit text after the paragraph.

Optional terms may apply.

Final implicit text at the end.

Remaining text.
"""
    
    result = strip_matches(root, license_text)
    assert result is not None
    assert "remaining text" in result.lower()
    assert "mixed license" not in result.lower()
    assert "some implicit license text" not in result.lower()
    assert "explicit paragraph" not in result.lower()
    assert "more implicit text" not in result.lower()
    assert "optional terms" not in result.lower()
    assert "final implicit text" not in result.lower()


def test_strip_matches_with_alt_elements():
    """Test strip_matches with top-level alt elements (like Multics.xml)."""
    from spdx_matcher.strip_matches import strip_matches
    
    # Create XML similar to Multics.xml with top-level alt elements
    xml_string = """<SPDXLicenseCollection xmlns="http://www.spdx.org/license">
        <license licenseId="Multics" name="Multics License">
            <text>
                <titleText>
                    <p>Multics License</p>
                </titleText>
                <optional>
                    <p>Historical Background</p>
                </optional>
                <optional>
                    <p>.</p>
                </optional>
                <alt match="-*" name="divider">
                -----------------------------------------------------------
                </alt>
                <p>Permission is hereby granted to use this software.</p>
            </text>
        </license>
    </SPDXLicenseCollection>"""
    
    root = ET.fromstring(xml_string)
    
    # Test with alt element present (using dashes)
    license_text_with_alt = """Multics License

Historical Background

.

-----------------------------------------------------------

Permission is hereby granted to use this software.

Remaining text.
"""
    
    result1 = strip_matches(root, license_text_with_alt)
    assert result1 is not None
    assert "remaining text" in result1.lower()
    assert "multics license" not in result1.lower()
    assert "historical background" not in result1.lower()
    assert "---" not in result1
    assert "permission is hereby granted" not in result1.lower()
    
    # Test with alt element using different pattern (should also match due to alt match pattern)
    license_text_alt_variation = """Multics License

Historical Background

.

---------

Permission is hereby granted to use this software.

Remaining text.
"""
    
    result2 = strip_matches(root, license_text_alt_variation)
    assert result2 is not None
    assert "remaining text" in result2.lower()
    assert "multics license" not in result2.lower()
    assert "historical background" not in result2.lower()
    assert "---------" not in result2
    assert "permission is hereby granted" not in result2.lower()
    
    # Test without optional elements but with alt element
    license_text_minimal = """Multics License

-----------------------------------------------------------

Permission is hereby granted to use this software.

Remaining text.
"""
    
    result3 = strip_matches(root, license_text_minimal)
    assert result3 is not None
    assert "remaining text" in result3.lower()
    assert "multics license" not in result3.lower()
    assert "---" not in result3
    assert "permission is hereby granted" not in result3.lower()
