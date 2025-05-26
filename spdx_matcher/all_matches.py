from typing import List, Tuple

from spdx_matcher.license_loader import load_licenses
from spdx_matcher.strip_matches import strip_matches


def find_all_matches(license_text: str, verbose: bool = False) -> List[Tuple[str, str]]:
    """
    Try to match license text against all available SPDX license templates.

    Args:
        license_text: The license text to match
        verbose: If True, print progress information

    Returns:
        List of tuples (license_id, remaining_text) for successful matches.
        remaining_text is None if match failed, otherwise it's the unmatched portion.
    """
    matches = []
    licenses = load_licenses()

    if verbose:
        print(f"Testing against {len(licenses)} license templates...")

    for i, (license_id, tree) in enumerate(licenses.items()):

        print(f"Testing license {i + 1}/{len(licenses)}: {license_id}")

        # Try to match
        result = strip_matches(tree, license_text)

        if result is not None:
            matches.append((license_id, result))
            if verbose:
                remaining_chars = len(result.strip()) if result else 0
                print(f" Match found: {license_id} (remaining: {remaining_chars} chars)")

    return matches


def find_best_matches(license_text: str, verbose: bool = False) -> List[Tuple[str, str, int]]:
    """
    Find the best matching SPDX licenses by amount of text matched.

    Args:
        license_text: The license text to match
        max_results: Maximum number of results to return
        verbose: If True, print progress information

    Returns:
        List of tuples (license_id, remaining_text, remaining_char_count)
        sorted by fewest remaining characters (best matches first).
    """
    matches = find_all_matches(license_text, verbose)

    # Calculate remaining character counts and sort
    scored_matches = []
    for license_id, remaining_text in matches:
        remaining_chars = len(remaining_text.strip()) if remaining_text else 0
        scored_matches.append((license_id, remaining_text, remaining_chars))

    # Sort by remaining characters (ascending - fewer remaining = better match)
    scored_matches.sort(key=lambda x: x[2])

    return scored_matches
