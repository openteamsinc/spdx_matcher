import re
from typing import List, Optional

from lxml.etree import _Element as Element

from .matchers import (
    BaseMatcher,
    BulletMatcher,
    LicenseMatcher,
    ListMatcher,
    Matcher,
    OptionalMatcher,
    RegexMatcher,
    TitleMatcher,
    TransformResult,
)
from .normalize import normalize


def make_xpath(elem: Element) -> str:
    """Generate xpath for an element by walking up the tree."""
    path = []
    current: Optional[Element] = elem

    while current is not None:
        tag = current.tag.split("}")[-1] if "}" in current.tag else current.tag

        # Add position predicate for specificity
        parent = current.getparent()
        if parent is not None:
            siblings = [c for c in parent if c.tag == current.tag]
            if len(siblings) > 1:
                position = siblings.index(current) + 1
                tag = f"{tag}[{position}]"

        path.append(tag)
        current = parent

    return "/" + "/".join(reversed(path)) if path else "/"


class XMLToRegexTransformer:

    def transform(self, element: Element) -> TransformResult:
        tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
        handler_method_name = f"_transform_{tag}"
        handler = getattr(self, handler_method_name)
        matcher = handler(element)
        if isinstance(matcher, BaseMatcher):
            matcher = matcher.simplify()

        return matcher

    def _transform_p(self, element: Element) -> TransformResult:
        parts: List[TransformResult] = []

        if element.text:
            parts.append(normalize(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            if child_result:
                parts.append(child_result)

            if child.tail:

                tail = normalize(child.tail.strip())
                parts.append(tail)
        return Matcher(parts=parts, xpath=make_xpath(element))

    def _transform_alt(self, element: Element) -> RegexMatcher:
        match_pattern = element.get("match")
        assert match_pattern
        return RegexMatcher(regex=match_pattern, xpath=make_xpath(element))

    def _transform_optional(self, element: Element) -> OptionalMatcher:
        parts: List[TransformResult] = []

        if element.text:
            parts.append(normalize(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            parts.append(child_result)

            if child.tail:
                parts.append(normalize(child.tail.strip()))

        return OptionalMatcher(parts=parts, xpath=make_xpath(element))

    def _transform_text(self, element: Element) -> LicenseMatcher:
        parts: List[TransformResult] = []
        title: Optional[TransformResult] = None
        # copyright: Optional[TransformResult] = None

        if element.text:
            parts.append(normalize(element.text.strip()))

        for child in element:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            child_result = self.transform(child)

            if tag in ["titleText", "copyrightText"]:
                if tag == "titleText":
                    title = child_result
                continue
            else:
                # Ignore because we want to match any line starting with copyright
                # copyright = child_result

                parts.append(child_result)

            if child.tail:
                parts.append(normalize(child.tail.strip()))

        copyright = RegexMatcher(
            regex=r"^\s*copyright.*", xpath=make_xpath(element), flags=re.IGNORECASE | re.MULTILINE
        )

        return LicenseMatcher(title=title, copyright=copyright, parts=parts, xpath=make_xpath(element))

    def _transform_titleText(self, element: Element) -> Matcher:
        parts: List[TransformResult] = []
        if element.text:
            r = normalize(element.text.strip())
            parts.append(r)
        for child in element:

            text = self.transform(child)
            if text:
                parts.append(text)

        return TitleMatcher(parts=parts, xpath=make_xpath(element))

    def _transform_copyrightText(self, element: Element) -> TransformResult:
        parts: List[TransformResult] = []
        for child in element:
            text = self.transform(child)
            if text:
                parts.append(text)
        # Match anything ... not used in license
        return RegexMatcher(regex=r".*", xpath=make_xpath(element), flags=re.IGNORECASE | re.MULTILINE)

    def _transform_list(self, element: Element) -> ListMatcher:
        parts: List[TransformResult] = []

        if element.text:
            parts.append(normalize(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            parts.append(child_result)

            if child.tail:
                parts.append(normalize(child.tail.strip()))

        return ListMatcher(parts=parts, xpath=make_xpath(element))

    def _transform_item(self, element: Element) -> Matcher:
        parts: List[TransformResult] = []

        if element.text:
            parts.append(normalize(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            parts.append(child_result)

            if child.tail:
                parts.append(normalize(child.tail.strip()))
        return Matcher(parts=parts, xpath=make_xpath(element))

    def _transform_bullet(self, element: Element) -> BulletMatcher:
        return BulletMatcher(xpath=make_xpath(element))

    def _transform_br(self, element: Element) -> str:
        return " "

    def _transform_standardLicenseHeader(self, element: Element) -> Matcher:
        parts: List[TransformResult] = []

        if element.text:
            parts.append(normalize(element.text.strip()))

        for child in element:
            child_result = self.transform(child)
            if child_result:
                parts.append(child_result)

            if child.tail:
                parts.append(normalize(child.tail.strip()))

        return Matcher(parts=parts, xpath=make_xpath(element))

    def _transform_SPDXLicenseCollection(self, element: Element) -> LicenseMatcher:
        children = element
        assert len(children) == 1, "SPDXLicenseCollection should have exactly one child element"
        child = children[0]
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        assert tag == "license", "Child of SPDXLicenseCollection should be a license element"
        result = self.transform(child)
        assert isinstance(result, LicenseMatcher), f"Result should be a LicenseMatcher (got {type(result)})"
        return result

    def _transform_license(self, element: Element) -> LicenseMatcher:
        children = element
        child_tags = [child.tag.split("}")[-1] if "}" in child.tag else child.tag for child in children]
        assert "text" in child_tags, f"License element should have a text child, found: {child_tags}"

        child = children[child_tags.index("text")]

        result = self.transform(child)
        assert isinstance(result, LicenseMatcher), f"Result should be a LicenseMatcher (got {type(result)})"
        result.name = str(element.attrib.get("name"))
        result.kind = element.attrib.get("kind")
        result.restrictions = [r for r in element.attrib.get("restrictions", "").split("|") if r.strip()]
        result.is_osi_approved = element.attrib.get("isOsiApproved", "false").lower() == "true"
        return result


def transform(element: Element, transformer: Optional[XMLToRegexTransformer] = None) -> LicenseMatcher:
    if transformer is None:
        transformer = XMLToRegexTransformer()
    t = transformer.transform(element)
    assert isinstance(t, LicenseMatcher), "Transformed result should be a LicenseMatcher"
    return t
