from typing import List
from functools import lru_cache
from .base_matcher import LicenseResult, NoMatchError
from .license_loader import load_licenses
from .transformer import transform
from .normalize import normalize


@lru_cache
def load_license_matchers():
    licenses = load_licenses()
    return {k: transform(v) for k, v in licenses.items()}


def find_license(text: str, stop_on_perfect=True) -> List[dict]:
    normalized_text = normalize(text)
    license_matchers = load_license_matchers()
    results = []

    for spdx_id, matcher in license_matchers.items():
        r = LicenseResult(normalized_text)
        try:
            matcher.match(r)
        except NoMatchError:
            continue

        results.append(
            {
                "spdx_id": spdx_id,
                "extra_characters": r.text,
                "restrictions": matcher.restrictions,
                "name": matcher.name,
                "kind": matcher.kind,
                "is_osi_approved": matcher.is_osi_approved,
            }
        )
        if len(r.text) == 0 and stop_on_perfect:
            return sorted(results, key=lambda x: len(x["extra_characters"]))
    return sorted(results, key=lambda x: len(x["extra_characters"]))
