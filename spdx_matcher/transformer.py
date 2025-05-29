from xml.etree.ElementTree import Element
from .regexes import apply_all_replacers, bullet_replacer, copyright_symbol_replacer
from typing import Optional, List
from .types import Matcher, LicenseMatcher, TransformResult, ListMatcher


def make_xpath(elem: Element) -> str:
    """Generate xpath for an element by walking up the tree."""
    path = []
    current = elem
    while current is not None:
        tag = current.tag.split("}")[-1] if "}" in current.tag else current.tag
        path.append(tag)
        current = current.getparent() if hasattr(current, "getparent") else None
    return "/" + "/".join(reversed(path)) if path else "/"


class XMLToRegexTransformer:

    def transform(self, element: Element) -> TransformResult:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        handler_method_name = f"_transform_{tag}"
        handler = getattr(self, handler_method_name)
        matcher = handler(element)
        # if type(matcher) is Matcher and len(matcher.parts) == 1 and isinstance(matcher.parts[0], str):
        #     return r"\s*".join(matcher.parts)  # type: ignore
        if type(matcher) is Matcher and all(isinstance(part, str) for part in matcher.parts):
            return r"\s*".join(matcher.parts)  # type: ignore
        return matcher

    def _transform_p(self, element: Element) -> TransformResult:
        parts: List[TransformResult] = []

        if element.text:
            parts.append(apply_all_replacers(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            if child_result:
                parts.append(child_result)

            if child.tail:
                parts.append(apply_all_replacers(child.tail.strip()))

        return Matcher(parts=parts, xpath=make_xpath(element))

    def _transform_alt(self, element: Element) -> str:
        match_pattern = element.get("match")
        assert match_pattern
        return f"({match_pattern})"

    def _transform_optional(self, element: Element) -> str:
        parts: List[str] = []

        if element.text:
            parts.append(apply_all_replacers(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            if child_result:
                assert isinstance(child_result, str), "Child result must be a string for optional transformation"
                parts.append(child_result)

            if child.tail:
                parts.append(apply_all_replacers(child.tail.strip()))

        assert len(parts), "Optional element must have at least one part"

        content = r"\s*".join(parts)
        return f"({content})?"

    def _transform_text(self, element: Element) -> LicenseMatcher:
        parts: List[TransformResult] = []
        title: Optional[TransformResult] = None
        copyright: Optional[TransformResult] = None

        for child in element:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            child_result = self.transform(child)
            if tag == "titleText":
                title = child_result
                continue
            if tag == "copyrightText":
                copyright = child_result
                continue

            parts.append(child_result)

        return LicenseMatcher(title=title, copyright=copyright, parts=parts, xpath=make_xpath(element))

    def _transform_titleText(self, element: Element) -> Matcher:
        parts: List[TransformResult] = []
        if element.text:
            r = apply_all_replacers(element.text.strip())
            parts.append(r)
        for child in element:

            text = self.transform(child)
            if text:
                parts.append(text)

        return Matcher(parts=parts, xpath=make_xpath(element))

    def _transform_copyrightText(self, element: Element) -> TransformResult:
        parts: List[TransformResult] = []
        for child in element:
            text = self.transform(child)
            if text:
                parts.append(text)
        return f'^\s*{copyright_symbol_replacer("copyright")}.*?(?=\n\s*\n|$)'

    def _transform_list(self, element: Element) -> ListMatcher:
        parts: List[TransformResult] = []

        if element.text:
            parts.append(apply_all_replacers(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            parts.append(child_result)

            if child.tail:
                parts.append(apply_all_replacers(child.tail.strip()))

        return ListMatcher(parts=parts, xpath=make_xpath(element))

    def _transform_item(self, element: Element) -> str:
        parts = []

        if element.text:
            parts.append(apply_all_replacers(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            if isinstance(child_result, str) and child_result:
                parts.append(child_result)

            if child.tail:
                parts.append(apply_all_replacers(child.tail.strip()))

        content = r"\s*".join(filter(None, parts))
        return content

    def _transform_bullet(self, element: Element) -> str:
        return bullet_replacer()

    def _transform_SPDXLicenseCollection(self, element: Element) -> LicenseMatcher:
        children = list(element)
        assert len(children) == 1, "SPDXLicenseCollection should have exactly one child element"
        child = children[0]
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        assert tag == "license", "Child of SPDXLicenseCollection should be a license element"
        result = self.transform(child)
        assert isinstance(result, LicenseMatcher), "Result should be a LicenseMatcher"
        return result

    def _transform_license(self, element: Element) -> LicenseMatcher:
        children = list(element)
        assert len(children) == 2, "License should have exactly one child element"
        child = children[1]
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        assert tag == "text", "Child of license should be a text element"
        result = self.transform(child)
        assert isinstance(result, LicenseMatcher), "Result should be a LicenseMatcher"
        return result


def element_to_regex(element: Element, transformer: Optional[XMLToRegexTransformer] = None) -> TransformResult:
    if transformer is None:
        transformer = XMLToRegexTransformer()
    return transformer.transform(element)
