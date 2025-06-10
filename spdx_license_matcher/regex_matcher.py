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


def assemble_regex_parts(part: TransformResult, parts: List[TransformResult]) -> TransformResult:
    if not parts:
        return part

    if not isinstance(part, RegexMatcher):
        return part

    while parts:
        next_part = parts.pop(0)
        pattern = part.regex
        pattern_option = "?" if part.optional else ""
        # if part.optional:
        #     pattern = f"({pattern})?"
        # if pattern in [".+", ".*"]:
        #     pattern += "?"

        if isinstance(next_part, RegexMatcher):
            next_pattern = next_part.regex
            if next_part.optional:
                next_pattern = f"({next_pattern})?"
            # if next_pattern in [".+", ".*"]:
            #     next_pattern += "?"

            part = RegexMatcher(
                regex=f"({pattern}){pattern_option}[^\\S\r\n]*{next_pattern}",
                xpath=part.xpath,
                flags=part.flags | next_part.flags,
            )
        elif isinstance(next_part, str):
            return RegexMatcher(regex=f"({pattern}){pattern_option}[^\\S\r\n]*{re.escape(next_part)}", xpath=part.xpath)
        else:
            parts.insert(0, next_part)  # Put it back if it's not a RegexMatcher or str
            # wrap the current part in parentheses
            return RegexMatcher(
                regex=f"({pattern}){pattern_option}",
                xpath=part.xpath,
                flags=part.flags,
            )

    return part
