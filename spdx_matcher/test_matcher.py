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
