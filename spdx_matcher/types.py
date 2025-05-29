from dataclasses import dataclass
from typing import List, Optional, Union
import re
import logging

logger = logging.getLogger(__name__)


TransformResult = Union["Matcher", str]


@dataclass
class Matcher:
    parts: List[TransformResult]
    xpath: str


@dataclass
class ListMatcher(Matcher):
    pass


@dataclass
class LicenseMatcher(Matcher):
    copyright: Optional[TransformResult]
    title: Optional[TransformResult]
