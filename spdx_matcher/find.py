from typing import List, Tuple
from functools import lru_cache
from .base_matcher import LicenseResult, NoMatchError
from .license_loader import load_licenses
from .transformer import transform
from .normalize import normalize


@lru_cache
def load_license_matchers():
    licenses = load_licenses()
    return {k: transform(v) for k, v in licenses.items()}


def find_license(text: str) -> List[Tuple[str, int]]:
    normalized_text = normalize(text)
    license_matchers = load_license_matchers()
    results = []

    for name, matcher in license_matchers.items():
        r = LicenseResult(normalized_text)
        try:
            matcher.match(r)
        except NoMatchError:
            continue
        results.append((name, len(r.text)))
    return sorted(results, key=lambda x: x[1])
