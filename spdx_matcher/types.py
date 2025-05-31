from dataclasses import dataclass
from typing import List, Optional, Union, Any
import logging
import re

log = logging.getLogger(__name__)


TransformResult = Union["BaseMatcher", str]


def to_dict(tr: Optional[TransformResult]) -> Any:
    if isinstance(tr, str):
        return tr

    if tr is None:
        return None

    return tr.to_dict()


def match(tr: TransformResult, text: str) -> str | None:
    if isinstance(tr, str):
        log.debug(f"Matching string:\n\t{tr!r}\n\nin text:\n\t{text!r}")
        if tr not in text:
            log.debug("String not found in text.")
            return None
        log.debug("String found, removing it from text.")
        return text.replace(tr, "", 1)

    return tr.match(text)


@dataclass
class BaseMatcher:
    xpath: str


@dataclass
class BulletMatcher:
    xpath: str

    def match(self, text: str) -> str:
        if " • " in text:
            log.debug("Bullet point found, removing it from text.")
            return text.replace(" • ", "", 1)
        return text

    def to_dict(self) -> Any:
        return {
            "kind": "bullet",
        }


@dataclass
class Matcher(BaseMatcher):
    parts: List[TransformResult]

    def match(self, text: str):

        parts = list(self.parts)
        while parts:
            part = parts.pop(0)
            if isinstance(part, RegexMatcher) and parts:
                next_part = parts.pop(0)
                assert isinstance(next_part, str)
                part = RegexMatcher(regex=f"({part.regex})\\s*{re.escape(next_part)}", xpath=part.xpath)

            new_text = match(part, text)
            if new_text is None:
                return None
            text = new_text
        return text

    def to_dict(self):
        return {
            "kind": "matcher",
            "parts": [to_dict(part) if isinstance(part, BaseMatcher) else part for part in self.parts],
        }


@dataclass
class ListMatcher(Matcher):
    pass


@dataclass
class RegexMatcher(BaseMatcher):
    regex: str
    flags: int = re.IGNORECASE

    def to_dict(self) -> Any:
        return {
            "kind": "regex",
            "regex": self.regex,
        }

    def match(self, text: str) -> str | None:

        log.debug(f"Matching regex:\n\t{self.regex!r}\n\nin text:\n\t{text!r}")
        match = re.search(self.regex, text, self.flags)
        if not match:
            log.debug("Regex not found in text.")
            return None
        log.debug(f"Regex found, removing it from text: {match.group(0)!r}")
        return text[: match.start()] + text[match.end() :]


@dataclass
class OptionalMatcher(Matcher):
    def to_dict(self) -> Any:
        return {
            "kind": "optional",
            "parts": [to_dict(part) for part in self.parts if part],
        }

    def match(self, text: str):
        result = super().match(text)
        if result is None:
            return text
        return result


@dataclass
class LicenseMatcher(Matcher):
    copyright: Optional[TransformResult]
    title: Optional[TransformResult]

    def match(self, text: str):
        if self.title:
            new_text = match(self.title, text)
            if new_text is not None:
                text = new_text

        if self.copyright:
            while True:
                new_text = match(self.copyright, text)
                if new_text is None:
                    break
                text = new_text

        return super().match(text)

    def to_dict(self):
        return {
            "kind": "license",
            "title": to_dict(self.title),
            "copyright": to_dict(self.copyright),
            "parts": [to_dict(part) for part in self.parts if part],
        }
