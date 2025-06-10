import logging
import re
from dataclasses import dataclass
from typing import Any, List, Union

log = logging.getLogger(__name__)


@dataclass
class BaseMatcher:
    xpath: str

    def match(self, result: "LicenseResult", optional: bool) -> bool:
        raise NotImplementedError("Subclasses must implement the match method.")

    def to_dict(self) -> Any:
        raise NotImplementedError("Subclasses must implement the to_dict method.")

    def simplify(self):
        return self

    def is_empty(self):
        return False


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

    def trim_remaining(self):
        self.rewind()
        self.text = self.text.strip()
        # if text only contains non letter characters
        if not re.search(r"[a-zA-Z]", self.text):
            log.debug("Text only contains non-letter characters, setting to empty string.")
            self.text = ""

    def rewind(self):

        skipped = "\n".join(self.skipped)
        log.debug(f"Rewinding text:\n\t{skipped!r}")
        self.text = "\n".join([skipped, self.text])
        self.skipped = []

    def match(self, tr: TransformResult, optional=False) -> bool:

        text = self.text.strip()
        if isinstance(tr, str):
            log.debug(f"Matching {'optional' if optional else ''} string:\n\t{tr!r}")
            if tr not in text:
                log.debug(f"❌ String not found in text\n\nin text:\n\t{text!r}")
                if optional:
                    return False
                raise NoMatchError(f"String {tr!r} not found in text {text!r}")

            idx = text.index(tr)
            if optional and idx > 0:
                log.debug("❓ Optional string found, but not at the start of the text.")
                return False

            log.debug("✅ String found, removing it from text")

            skipped = text[:idx].strip()
            if skipped:
                log.debug(f"Skipped text: {skipped!r}")
                self.skipped.append(skipped)

            new_text = text[idx:].replace(tr, "", 1)
            self.text = new_text
            return True

        return tr.match(self, optional=optional)

    def match_and_consume_line(self, tr: TransformResult, optional=True) -> bool:
        text = self.text.strip()
        lines = text.splitlines()
        assert isinstance(tr, str), f"tr must be a string for match_and_consume_line (got {type(tr)})"
        log.debug(f"Matching {'optional' if optional else ''} string line:\n\t{tr!r}")
        for i, line in enumerate(lines):
            if tr in line:
                log.debug("✅ String found, removing entire line from text")
                result = lines[:i] + lines[i + 1 :]
                self.text = "\n".join(result).strip()
                return True

        log.debug(f"❌ String not found in text\n\nin text:\n\t{text!r}")
        if optional:
            return False
        raise NoMatchError(f"String {tr!r} not found in text {text!r}")

    def regex(self, pattern, flags, optional=False) -> bool:
        log.debug(f"Matching regex:\n\t{pattern!r}")
        assert isinstance(pattern, str), "Pattern must be a string"

        match = re.search(pattern, self.text, flags)
        if not match:
            log.debug(f"❌ Regex not found in text:\n\t{self.text!r}")
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

    def __repr__(self):
        return f"LicenseResult(text={self.text!r}, skipped={self.skipped!r}, wont_match={self.wont_match!r})"
