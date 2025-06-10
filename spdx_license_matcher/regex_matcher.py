import re
from dataclasses import dataclass
from typing import Any, List, Tuple

from .base_matcher import BaseMatcher, LicenseResult, TransformResult


@dataclass
class RegexMatcher(BaseMatcher):
    regex: str
    flags: int = re.IGNORECASE
    optional: bool = False

    def to_dict(self) -> Any:
        return {
            "kind": "regex",
            "regex": self.regex,
            "xpath": self.xpath,
        }

    def match(self, result: LicenseResult, optional: bool = False) -> bool:
        return result.regex(self.regex, flags=self.flags, optional=optional or self.optional)


def regex_string(part: TransformResult) -> Tuple[str, bool, int]:
    if isinstance(part, str):
        return re.escape(part), False, 0
    if isinstance(part, RegexMatcher):
        return part.regex, part.optional, part.flags
    raise ValueError(f"Unsupported part type: {type(part)}. Expected str or RegexMatcher.")


def wrap_if_optional(pat: str, optional: bool) -> str:
    if optional:
        return f"({pat})?"
    return pat


def merge_two_regex_parts(partA: TransformResult, partB: TransformResult) -> TransformResult:
    regex_a, optional_a, flags_a = regex_string(partA)
    regex_b, optional_b, flags_b = regex_string(partB)

    merged_regex = f"{wrap_if_optional(regex_a, optional_a)}\\s*{wrap_if_optional(regex_b, optional_b)}"
    return RegexMatcher(xpath="", regex=merged_regex, flags=flags_a | flags_b, optional=False)


def merge_regex_parts(parts: List[TransformResult]) -> List[TransformResult]:
    new_parts = list(parts)
    i = 0
    while i < len(new_parts) - 1:
        partA = new_parts[i]
        partB = new_parts[i + 1]
        if isinstance(partA, RegexMatcher) and isinstance(partB, (str, RegexMatcher)):
            partC = merge_two_regex_parts(partA, partB)
            new_parts = new_parts[:i] + [partC] + new_parts[i + 2 :]
        else:
            i += 1
    return new_parts
