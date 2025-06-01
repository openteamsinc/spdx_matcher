from typing import Any, List
import re
from dataclasses import dataclass
from .base_matcher import BaseMatcher, TransformResult, LicenseResult


@dataclass
class RegexMatcher(BaseMatcher):
    regex: str
    flags: int = re.IGNORECASE

    def to_dict(self) -> Any:
        return {
            "kind": "regex",
            "regex": self.regex,
            "xpath": self.xpath,
        }

    def match(self, result: LicenseResult, optional: bool = False) -> bool:
        return result.regex(self.regex, flags=self.flags, optional=optional)


def assemble_regex_parts(part: TransformResult, parts: List[TransformResult]) -> TransformResult:
    if not parts:
        return part

    if not isinstance(part, RegexMatcher):
        return part

    while parts:
        next_part = parts.pop(0)
        pattern = part.regex
        # if pattern in [".+", ".*"]:
        #     pattern += "?"

        if isinstance(next_part, RegexMatcher):
            next_pattern = next_part.regex
            # if next_pattern in [".+", ".*"]:
            #     next_pattern += "?"

            part = RegexMatcher(
                regex=f"({pattern})[^\\S\r\n]*{next_pattern}",
                xpath=part.xpath,
                flags=part.flags | next_part.flags,
            )
        elif isinstance(next_part, str):
            return RegexMatcher(regex=f"({pattern})[^\\S\r\n]*{re.escape(next_part)}", xpath=part.xpath)
        else:
            parts.insert(0, next_part)  # Put it back if it's not a RegexMatcher or str
            # wrap the current part in parentheses
            return RegexMatcher(
                regex=f"({part.regex})",
                xpath=part.xpath,
                flags=part.flags,
            )

    return part
