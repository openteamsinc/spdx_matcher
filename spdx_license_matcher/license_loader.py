import logging
from importlib.abc import Traversable
from importlib.resources import files
from typing import Dict, Optional, Tuple

from lxml import etree
from lxml.etree import _Element as Element

log = logging.getLogger(__name__)


def load_license(license_filename: str) -> Element:
    license_file = files("spdx_license_matcher.licenses").joinpath(license_filename)
    _, root = load_license_from_traversable(license_file)
    return root


def load_license_from_traversable(license_file: Traversable) -> Tuple[Optional[str], Element]:

    with license_file.open("rb") as fd:
        data = fd.read()
    root = etree.fromstring(data)

    #     # Extract license information
    #     # The {http://www.spdx.org/license} prefix is due to XML namespace
    ns = "{http://www.spdx.org/license}"
    license_elem = root.find(f".//{ns}license")

    if license_elem is None:
        return None, root
    license_id = license_elem.get("licenseId")
    if license_id is None:
        return None, root

    return license_id, root


def load_licenses() -> Dict[str, Element]:
    """
    Load all SPDX license XML files from the specified directory into a dictionary.

    Args:
        license_dir: Path to the directory containing SPDX license XML files

    Returns:
        Dictionary with SPDX IDs as keys and license data as values
    """
    licenses: Dict[str, Element] = {}

    for filename in files("spdx_license_matcher.licenses").iterdir():
        if not filename.is_file():
            continue
        if not filename.name.endswith(".xml"):
            continue

        license_id, root = load_license_from_traversable(filename)
        if license_id:
            if license_id in licenses:
                log.warning(f"Duplicate license ID found: {license_id} in {filename.name}")
            licenses[license_id] = root
        else:
            log.warning(f"License ID not found in {filename.name}, skipping.")

    return licenses
