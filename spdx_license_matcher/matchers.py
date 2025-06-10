import logging
import re
from dataclasses import dataclass, field, replace
from typing import Any, List, Optional

from .base_matcher import BaseMatcher, LicenseResult, TransformResult
from .matcher_utils import is_empty, to_dict
from .regex_matcher import RegexMatcher, merge_regex_parts

log = logging.getLogger(__name__)


@dataclass
class BulletMatcher(BaseMatcher):
    xpath: str

    def match(self, result: LicenseResult, optional: bool) -> bool:
        result.regex(
            r"^\s*([0-9]+(\.[0-9]+)+|[a-z0-9]+(\.[0-9]+)*[\.\)]|[\.\-*•]|\([a-z0-9]+\)|\[[a-z0-9]+\])\s+",
            flags=re.IGNORECASE,
            optional=True,
        )
        return True

    def to_dict(self) -> Any:
        return {
            "kind": "bullet",
            "xpath": self.xpath,
        }


@dataclass
class Matcher(BaseMatcher):
    parts: List[TransformResult]

    def __init__(self, xpath: str, parts: List[TransformResult]) -> None:
        self.xpath = xpath
        self.parts = [p for p in parts if not is_empty(p)]

    def match(self, result: LicenseResult, optional: bool) -> bool:

        parts = list(self.parts)
        while parts:
            part = parts.pop(0)
            # part = assemble_regex_parts(part, parts)
            did_match = result.match(part, optional=optional)
            if not optional and not did_match:

                return False

        result.strip()
        return True

    def to_dict(self):
        return {
            "kind": "matcher",
            "xpath": self.xpath,
            "parts": [to_dict(part) if isinstance(part, BaseMatcher) else part for part in self.parts],
        }

    def simplify(self):
        parts = [part for part in self.parts if not is_empty(part)]
        if len(parts) == 1 and type(parts[0]) is Matcher:
            parts = parts[0].parts

        parts = merge_regex_parts(parts)
        return replace(self, parts=parts)

    def is_empty(self):
        return len([p for p in self.parts if not is_empty(p)]) == 0


@dataclass
class ListMatcher(Matcher):
    pass


@dataclass
class TitleMatcher(Matcher):

    def match(self, result: LicenseResult, optional: bool) -> bool:
        if len(self.parts) == 1 and isinstance(self.parts[0], str):
            return result.match_and_consume_line(self.parts[0], optional=True)
        return super().match(result, optional)


@dataclass
class OptionalMatcher(Matcher):
    def to_dict(self) -> Any:
        return {
            "kind": "optional",
            "parts": [to_dict(part) for part in self.parts if part],
        }

    def match(self, result: LicenseResult, optional: bool = True) -> bool:
        did_match = super().match(result, optional=True)
        return did_match

    def simplify(self) -> TransformResult:
        other = super().simplify()
        if len(other.parts) == 1 and isinstance(other.parts[0], str):
            pattern = re.escape(other.parts[0])
            return RegexMatcher(xpath=self.xpath, regex=pattern, optional=True)
        return other


@dataclass
class LicenseMatcher(Matcher):
    copyright: Optional[TransformResult]
    title: Optional[TransformResult]
    name: Optional[str] = None
    kind: Optional[str] = None
    is_osi_approved: Optional[bool] = None
    restrictions: List[str] = field(default_factory=list)

    def match(self, result: LicenseResult, optional: bool = False) -> bool:

        super().match(result, optional=optional)

        result.rewind()

        if self.title:
            result.match(self.title, optional=True)

        if self.copyright:
            did_match = result.match(self.copyright, optional=True)
            while did_match:
                did_match = result.match(self.copyright, optional=True)

        result.trim_remaining()
        return True

    def to_dict(self):
        return {
            "kind": "license",
            "title": to_dict(self.title),
            "copyright": to_dict(self.copyright),
            "parts": [to_dict(part) for part in self.parts if not is_empty(part)],
        }
