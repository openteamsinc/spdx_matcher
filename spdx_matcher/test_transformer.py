import re
import xml.etree.ElementTree as ET
from .transformer import XMLToRegexTransformer, element_to_regex


def test_transform_p_simple_text():
    xml = "<p>hello world</p>"
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    pattern = re.compile(result)
    assert pattern.match("hello world")
    assert pattern.match("hello    world")


def test_transform_p_with_alt():
    xml = '<p>hello <alt match="world|universe">world</alt></p>'
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    pattern = re.compile(result)
    assert pattern.match("hello world")
    assert pattern.match("hello universe")
    assert pattern.match("hello   world")


def test_transform_p_mixed_content():
    xml = '<p>hello <alt match="beautiful|wonderful">beautiful</alt> world</p>'
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    pattern = re.compile(result)
    assert pattern.match("hello beautiful world")
    assert pattern.match("hello wonderful world")
    assert pattern.match("hello   beautiful   world")


def test_transform_alt():
    xml = '<alt match="Software|Materials">Software</alt>'
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    assert result == "(Software|Materials)"
    pattern = re.compile(result)
    assert pattern.match("Software")
    assert pattern.match("Materials")


def test_transform_optional_simple():
    xml = "<optional>including the next paragraph</optional>"
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    pattern = re.compile(result)
    assert pattern.match("including the next paragraph")
    assert pattern.match("")


def test_transform_optional_with_nested_p():
    xml = "<optional><p>some text</p></optional>"
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    pattern = re.compile(result)
    assert pattern.match("some text")
    assert pattern.match("")


def test_element_to_regex_function():
    xml = "<p>test content</p>"
    element = ET.fromstring(xml)
    result = element_to_regex(element)

    pattern = re.compile(result)
    assert pattern.match("test content")


def test_complex_paragraph():
    xml = """<p>The <alt match="SOFTWARE IS|MATERIALS ARE">SOFTWARE IS</alt> provided "AS IS`</p>"""
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    pattern = re.compile(result)
    assert pattern.match('The SOFTWARE IS provided "AS IS"')
    assert pattern.match('The MATERIALS ARE provided "AS IS"')
    assert pattern.match('The   SOFTWARE IS   provided "AS IS"')


def test_paragraph_with_multiple_alts():
    xml = """<p>to deal in the
    <alt match="Software|Materials">Software</alt>
    without restriction, including the <alt match="Software|Materials">Software</alt>
    </p>"""
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    pattern = re.compile(result)
    assert pattern.match("to deal in the Software without restriction, including the Software")
    assert pattern.match("to deal in the Materials without restriction, including the Materials")
    assert pattern.match("to deal in the Software without restriction, including the Materials")


def test_transform_text():
    xml = """<text>
        <titleText><p>MIT License</p></titleText>
        <copyrightText><p>Copyright (c) 2023 Test</p></copyrightText>
        <p>Permission is granted</p>
        <p>The software is provided "AS IS"</p>
    </text>"""
    element = ET.fromstring(xml)
    transformer = XMLToRegexTransformer()
    result = transformer.transform(element)

    assert isinstance(result, dict)
    assert "title" in result
    assert "copyright" in result
    assert "parts" in result
    assert len(result["parts"]) == 2
