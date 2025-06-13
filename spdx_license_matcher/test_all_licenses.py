"""
Test license XML to text matching for all available licenses.
"""

import os

import pytest
from lxml import etree

from .base_matcher import LicenseResult, NoMatchError
from .matchers import LicenseMatcher
from .normalize import normalize
from .transformer import XMLToRegexTransformer

all_ids = {os.path.splitext(f)[0] for f in os.listdir("spdx_license_matcher/licenses/") if f.endswith(".xml")}

expected_failures = (
    {
        "MPEG-SSG",
        "TPL-1.0",
        "URT-RLE",
        "X11-swapped",
        "checkmk",
    }
    | {  # ?? wrong
        "MIT-testregex",
        "CC-BY-NC-SA-2.0-DE",
        "CC-BY-NC-ND-3.0-IGO",
    }
    | {  # some type of line prefix in text file
        "ssh-keyscan",
        "mpi-permissive",
        "SSH-OpenSSH",
    }
)

is_not_perfect = {
    "AAL",
    "Aladdin",
    "APL-1.0",
    "ASWF-Digital-Assets-1.1",
    "bcrypt-Solar-Designer",
    "Boehm-GC-without-fee",
    "BSD-Systemics-W3Works",
    "bzip2-1.0.6",
    "Catharon",
    "CC-BY-NC-SA-3.0-IGO",
    "CDLA-Permissive-1.0",
    "CDLA-Sharing-1.0",
    "CECILL-1.1",
    "CECILL-2.0",
    "CECILL-2.1",
    "CECILL-B",
    "CECILL-C",
    "COIL-1.0",
    "Cronyx",
    "DocBook-DTD",
    "DocBook-Stylesheet",
    "dtoa",
    "EUPL-1.0",
    "EUPL-1.1",
    "Fair",
    "FBM",
    "FDK-AAC",
    "FTL",
    "Game-Programming-Gems",
    "Glulxe",
    "GPL-2.0-or-later",
    "HDF5",
    "hdparm",
    "Hippocratic-2.1",
    "HPND-sell-regexpr",
    "HPND-sell-variant-MIT-disclaimer",
    "HPND",
    "InnoSetup",
    "JasPer-2.0",
    "lsof",
    "MakeIndex",
    "MIT-CMU",
    "mpich2",
    "MPL-1.0",
    "NBPL-1.0",
    "Net-SNMP",
    "NICTA-1.0",
    "Nokia",
    "NOSL",
    "OLDAP-1.1",
    "OLDAP-1.2",
    "OLDAP-1.3",
    "OLDAP-1.4",
    "OpenPBS-2.3",
    "PADL",
    "pnmstitch",
    "PPL",
    "psutils",
    "Python-2.0.1",
    "Qhull",
    "RPL-1.1",
    "SAX-PD-2.0",
    "SGI-B-1.0",
    "SOFA",
    "TORQUE-1.1",
    "TOSL",
    "TrustedQSL",
    "UMich-Merit",
    "UPL-1.0",
    "Wsuipa",
    "XSkat",
}


class NotPerfectMatchError(Exception):
    pass


def make_marks(license_id):
    if license_id in expected_failures:
        return [pytest.mark.xfail(reason=f"Known failure for {license_id}", strict=True, raises=NoMatchError)]

    if license_id in is_not_perfect:
        return [pytest.mark.xfail(reason=f"Perfect failure for {license_id}", strict=True, raises=NotPerfectMatchError)]

    return []


class TestAllLicenses:
    """Test license XML to text matching per SPDX guidelines."""

    @pytest.mark.parametrize(
        "license_id",
        [
            pytest.param(
                license_id,
                marks=make_marks(license_id),
            )
            for license_id in all_ids
        ],
    )
    def test_license_xml_to_text_matching(self, license_id):
        """Test that license XML can match against corresponding text file."""
        # Load XML file
        xml_path = f"spdx_license_matcher/licenses/{license_id}.xml"
        if not os.path.exists(xml_path):
            pytest.skip(f"XML file not found: {xml_path}")

        # Load text file
        txt_path = f"license-list-XML/test/simpleTestForGenerator/{license_id}.txt"
        if not os.path.exists(txt_path):
            pytest.skip(f"Text file not found: {txt_path}")

        # Load and parse XML
        with open(xml_path, "rb") as f:
            xml_data = f.read()
        root = etree.fromstring(xml_data, parser=None)

        # Load text content
        with open(txt_path) as f:
            license_text = f.read()
        license_text = normalize(license_text)
        license_result = LicenseResult(license_text)
        # Transform XML to matcher
        transformer = XMLToRegexTransformer()
        ns = "{http://www.spdx.org/license}"

        # Find the license element
        license_elem = root.find(f".//{ns}license")
        if license_elem is None:
            pytest.fail(f"No license element found in {license_id} XML")

        # Transform the license element to a matcher
        license_matcher = transformer.transform(license_elem)
        assert isinstance(license_matcher, LicenseMatcher)

        license_matcher.match(license_result)

        remaining_text = license_result.text.strip()
        if len(remaining_text):
            raise NotPerfectMatchError(f"Remaining: {remaining_text}")
