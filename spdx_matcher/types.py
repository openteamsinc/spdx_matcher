from dataclasses import dataclass
from typing import List, Optional, Union, Any
import logging
import re

log = logging.getLogger(__name__)

TransformResult = Union["BaseMatcher", str]


class NoMatchError(Exception):
    pass


class LicenseResult:
    skipped: List[str]
    text: str
    wont_match: List[Any]
    early_exit: bool

    def __init__(self, text: str, early_exit=True) -> None:
        self.text = text
        self.skipped = []
        self.wont_match = []
        self.early_exit = early_exit

    def strip(self):
        self.text = self.text.strip()

    def rewind(self):

        skipped = "\n".join(self.skipped)
        log.info(f"Rewinding text:\n\t{skipped!r}")
        self.text = "\n".join([skipped, self.text])
        self.skipped = []

    def match(self, tr: TransformResult, optional=False) -> bool:

        text = self.text.strip()
        if isinstance(tr, str):
            log.debug(f"Matching {'optional' if optional else ''} string:\n\t{tr!r}\n\nin text:\n\t{text!r}")
            if tr not in text:
                log.debug("❌ String not found in text")
                if optional:
                    return False
                raise NoMatchError(f"String {tr!r} not found in text {text!r}")
            log.debug("✅ String found, removing it from text")

            idx = text.index(tr)
            if optional and idx > 0:
                return False

            skipped = text[:idx].strip()
            if skipped:
                log.debug(f"Skipped text: {skipped!r}")
                self.skipped.append(skipped)

            new_text = text[idx:].replace(tr, "", 1)
            self.text = new_text
            return True

        return tr.match(self, optional=optional)

    def regex(self, pattern, flags, optional=False) -> bool:
        log.debug(f"Matching regex:\n\t{pattern!r}\n\nin text:\n\t{self.text!r}")
        assert isinstance(pattern, str), "Pattern must be a string"
        match = re.search(pattern, self.text, flags)
        if not match:
            log.debug("❌ Regex not found in text.")
            if optional:
                return False
            raise NoMatchError(f"Regex {pattern!r} not found in text {self.text!r}")

        log.debug(f"✅ Regex found, removing it from text: {match.group(0)!r}")
        skipped = self.text[: match.start()].strip()
        if skipped:
            log.debug(f"Skipped text: {skipped!r}")
            self.skipped.append(skipped)

        self.text = self.text[match.end() :].strip()
        return True


def to_dict(tr: Optional[TransformResult]) -> Any:
    if isinstance(tr, str):
        return tr

    if tr is None:
        return None

    return tr.to_dict()


@dataclass
class BaseMatcher:
    xpath: str

    def match(self, result: LicenseResult, optional: bool) -> bool:
        raise NotImplementedError("Subclasses must implement the match method.")

    def to_dict(self) -> Any:
        raise NotImplementedError("Subclasses must implement the to_dict method.")


@dataclass
class BulletMatcher:
    xpath: str

    def match(self, result: LicenseResult, optional: bool) -> bool:
        result.regex(
            r"^\s*([0-9]+(\.[0-9])?[\.\)]|[\.\-*•]|[abcdefgivx]+[\.\)]|\([abcdefgivx]+\)|\[[abcdefgivx]+\])\s+",
            flags=re.IGNORECASE,
            optional=True,
        )
        return True

    def to_dict(self) -> Any:
        return {
            "kind": "bullet",
            "xpath": self.xpath,
        }


def assemble_regex_parts(part: TransformResult, parts: List[TransformResult]) -> TransformResult:
    if not parts:
        return part

    if not isinstance(part, RegexMatcher):
        return part

    while parts:
        next_part = parts.pop(0)
        pattern = part.regex
        if pattern in [".+", ".*"]:
            pattern += "?"

        if isinstance(next_part, RegexMatcher):
            next_pattern = next_part.regex
            if next_pattern in [".+", ".*"]:
                next_pattern += "?"

            part = RegexMatcher(
                regex=f"({pattern})\\s*{next_pattern}",
                xpath=part.xpath,
                flags=part.flags | next_part.flags,
            )
        elif isinstance(next_part, str):
            return RegexMatcher(regex=f"({pattern})\\s*{re.escape(next_part)}", xpath=part.xpath)
        else:
            parts.insert(0, next_part)  # Put it back if it's not a RegexMatcher or str
            # wrap the current part in parentheses
            return RegexMatcher(
                regex=f"({part.regex})",
                xpath=part.xpath,
                flags=part.flags,
            )

    return part


def is_empty(p: Optional[TransformResult]) -> bool:
    if p is None:
        return True

    if isinstance(p, str):
        return not p.strip()

    if isinstance(p, Matcher):
        return not p.parts

    return False


@dataclass
class Matcher(BaseMatcher):
    parts: List[TransformResult]

    def __init__(self, xpath: str, parts: List[TransformResult]) -> None:
        self.xpath = xpath
        self.parts = [p for p in parts if not is_empty(p)]
        # if not self.parts:
        #     raise ValueError("Matcher must have at least one part.")

    def match(self, result: LicenseResult, optional: bool) -> bool:

        parts = list(self.parts)
        while parts:
            part = parts.pop(0)
            part = assemble_regex_parts(part, parts)
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


@dataclass
class ListMatcher(Matcher):
    pass


@dataclass
class RegexMatcher(BaseMatcher):
    regex: str
    flags: int = re.IGNORECASE

    # def __init__(self, regex: str, xpath: str, flags: int = re.IGNORECASE) -> None:
    #     self.regex = regex
    #     if regex == ".+":
    #         asfsf
    #     self.xpath = xpath
    #     self.flags = flags

    def to_dict(self) -> Any:
        return {
            "kind": "regex",
            "regex": self.regex,
            "xpath": self.xpath,
        }

    def match(self, result: LicenseResult, optional: bool = False) -> bool:
        return result.regex(self.regex, flags=self.flags, optional=optional)


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


@dataclass
class LicenseMatcher(Matcher):
    copyright: Optional[TransformResult]
    title: Optional[TransformResult]

    def match(self, result: LicenseResult, optional: bool = False) -> bool:

        super().match(result, optional=optional)

        result.rewind()

        if self.title:
            result.match(self.title, optional=True)

        if self.copyright:
            did_match = result.match(self.copyright, optional=True)
            while did_match:
                did_match = result.match(self.copyright, optional=True)

        return True

    def to_dict(self):
        return {
            "kind": "license",
            "title": to_dict(self.title),
            "copyright": to_dict(self.copyright),
            "parts": [to_dict(part) for part in self.parts if not is_empty(part)],
        }
