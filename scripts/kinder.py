#!/usr/bin/env python3

import os
import re
from collections import defaultdict

"""
License restrictions mapping for copyleft and reciprocal licenses.

Restriction types:
- derivative-work-copyleft: Entire derivative work must use same license
- network-copyleft: Network use/deployment triggers copyleft obligations
- library-copyleft: Only library modifications must use same license
- file-copyleft: Only modified files must use same license
- modification-disclosure: Must make modifications publicly available
- patent-grant: Includes patent licensing provisions
- commercial-restrictions: Limits or restricts commercial use
- choice-of-venue: Specifies legal jurisdiction for disputes
- deployment-trigger: Deployment (not just distribution) triggers obligations
- network-provisions: Special network use considerations
- user-data-access: Must provide users access to their own data
- cryptographic-autonomy: Cannot restrict user access to their cryptographic keys
- express-acceptance: Must obtain explicit license acceptance from recipients
- weak-copyleft: Limited copyleft applying only to specific components
- source-disclosure: Must provide source code access
- external-deployment: Network use treated as distribution
"""

restrictions = {
    # Strong copyleft licenses
    "AGPL": ["derivative-work-copyleft", "network-copyleft", "source-disclosure"],
    "GPL": ["derivative-work-copyleft", "source-disclosure"],
    "CECILL": ["derivative-work-copyleft", "choice-of-venue", "source-disclosure"],
    # Weak copyleft licenses
    "LGPL": ["library-copyleft", "source-disclosure"],
    "MPL": ["file-copyleft", "patent-grant"],
    "CDDL": ["file-copyleft", "patent-grant"],
    "EPL": ["file-copyleft", "patent-grant"],
    "EUPL": ["file-copyleft", "network-provisions"],
    # Specialized copyleft licenses
    "QPL": ["modification-disclosure", "commercial-restrictions", "choice-of-venue"],
    "RPL": ["modification-disclosure", "deployment-trigger", "patent-grant"],
    "OSL": ["derivative-work-copyleft", "source-disclosure"],
    # Network/data-focused licenses
    "CAL": [
        "derivative-work-copyleft",
        "network-copyleft",
        "user-data-access",
        "cryptographic-autonomy",
        "source-disclosure",
    ],
    # Permissive with special provisions
    "AFL": [
        "network-copyleft",
        "express-acceptance",
        "choice-of-venue",
        "external-deployment",
    ],
    "APSL": ["weak-copyleft", "patent-grant", "choice-of-venue", "source-disclosure"],
    # Standard permissive licenses (minimal restrictions)
    "Apache": ["patent-grant"],
    "BSD": [],
    "MIT": [],
    "Artistic": [],
    "CERN": [],
    "CNRI": [],
    "ECL": ["patent-grant"],
    "EFL": [],
    "LPL": [],
    "LPPL": [],
    "LiLiQ": [],
    "MulanPSL": ["patent-grant"],
    "OFL": [],
    "OLDAP": [],
    "PHP": [],
    "Python": [],
    "Unicode": [],
    "W3C": [],
    "ZPL": [],
}


def extract_kinds(directory):
    """Extract valid KINDs from filenames in directory."""
    files = [f for f in os.listdir(directory) if f.endswith(".xml")]
    kind_counts = defaultdict(int)

    for filename in files:
        # Extract potential KIND (everything before first hyphen)
        if "-" in filename:
            kind = filename.split("-")[0]
            if len(kind) >= 3:
                kind_counts[kind] += 1

    # Return KINDs that appear in multiple files
    return {kind for kind, count in kind_counts.items() if count > 1}


def process_license_file(filepath, kind):
    """Add kind attribute to license tag and write back."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        restriction = "|".join(restrictions.get(kind, []))
        # Replace <license with <license kind="KIND" restrictions=restrictions
        updated_content = re.sub(r"<license\b", f'<license kind="{kind}" restrictions="{restriction}"', content)

        if updated_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated_content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

    return False


def main():
    directory = "spdx_license_matcher/licenses"

    if not os.path.exists(directory):
        print(f"Directory {directory} not found")
        return

    # Extract valid KINDs
    valid_kinds = extract_kinds(directory)
    print(f"Found valid KINDs: {sorted(valid_kinds)}")

    # Process files for each KIND
    processed_count = 0
    for kind in valid_kinds:
        files = [f for f in os.listdir(directory) if f.startswith(f"{kind}-") and f.endswith(".xml")]

        print(f"\nProcessing {len(files)} files for KIND '{kind}':")
        for filename in files:
            filepath = os.path.join(directory, filename)
            if process_license_file(filepath, kind):
                print(f"  ✓ {filename}")
                processed_count += 1
            else:
                print(f"  ✗ {filename}")

    print(f"\nProcessed {processed_count} files total")


if __name__ == "__main__":
    main()
