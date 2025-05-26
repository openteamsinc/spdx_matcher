import xml.etree.ElementTree as ET
from typing import Dict, Any
from importlib.resources import files


def load_licenses() -> Dict[str, Any]:
    """
    Load all SPDX license XML files from the specified directory into a dictionary.

    Args:
        license_dir: Path to the directory containing SPDX license XML files

    Returns:
        Dictionary with SPDX IDs as keys and license data as values
    """
    licenses = {}

    # Register the namespace to avoid the ns0 prefix in element tags
    ET.register_namespace("", "http://www.spdx.org/license")

    for filename in files("spdx_matcher.licenses").iterdir():
        if not filename.is_file():
            continue
        if not filename.name.endswith(".xml"):
            continue
        with filename.open() as fd:
            tree = ET.parse(fd)
        root = tree.getroot()

        #     # Extract license information
        #     # The {http://www.spdx.org/license} prefix is due to XML namespace
        ns = "{http://www.spdx.org/license}"
        license_elem = root.find(f".//{ns}license")

        if license_elem is None:
            continue
        license_id = license_elem.get("licenseId")
        if license_id is None:
            continue

        licenses[license_id] = root

    return licenses
