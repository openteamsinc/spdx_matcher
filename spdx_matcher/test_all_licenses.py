"""
Test license XML to text matching for all available licenses.
"""

import pytest
import os
from lxml import etree
from .transformer import XMLToRegexTransformer
from .matchers import LicenseMatcher
from .base_matcher import NoMatchError, LicenseResult
from .normalize import normalize

all_ids = {os.path.splitext(f)[0] for f in os.listdir("license-list-XML/src/") if f.endswith(".xml")}

expected_failures = (
    {
        "Bitstream-Charter",
        "CC-BY-3.0-AU",
        "CC-BY-3.0-DE",
        "CC-BY-NC-3.0-DE",
        "CC-BY-NC-ND-3.0-DE",
        "CC-BY-NC-SA-2.0-DE",
        "CC-BY-NC-SA-3.0-DE",
        "CC-BY-NC-SA-3.0-IGO",
        "CC-BY-ND-3.0-DE",
        "CC-BY-SA-3.0-DE",
        "CC-PDM-1.0",
        "Community-Spec-1.0",
        "EPL-2.0",
        "EUPL-1.2",
        "LAL-1.3",
        "LiLiQ-Rplus-1.1",
        "MIT-testregex",
        "MPEG-SSG",
        "MPL-2.0-no-copyleft-exception",
        "NASA-1.3",
        "OGL-UK-1.0",
        "OGL-UK-2.0",
        "SSH-OpenSSH",
        "TPL-1.0",
        "URT-RLE",
        "X11-swapped",
        "checkmk",
        "copyleft-next-0.3.0",
        "copyleft-next-0.3.1",
        "dtoa",
        "radvd",
        "ssh-keyscan",
        "xlock",
    }
    | {  # Bad xml patterns
        "CAL-1.0",
        "CAL-1.0-Combined-Work-Exception",
    }
    | {
        "LPPL-1.3c",
        "Python-2.0.1",
        "LPPL-1.3a",
        "CC-BY-NC-SA-2.0-FR",
    }
    | {  # some type of line prefix
        "mpi-permissive",
        "MPL-2.0",
    }
)


class TestAllLicenses:
    """Test license XML to text matching per SPDX guidelines."""

    @pytest.mark.parametrize(
        "license_id",
        [
            (
                pytest.param(
                    license_id,
                    marks=pytest.mark.xfail(reason=f"Known failure for {license_id}", strict=True, raises=NoMatchError),
                )
                if license_id in expected_failures
                else license_id
            )
            for license_id in all_ids
        ],
    )
    def test_license_xml_to_text_matching(self, license_id):
        """Test that license XML can match against corresponding text file."""
        # Load XML file
        xml_path = f"license-list-XML/src/{license_id}.xml"
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
        # assert result is not None, f"Failed to match {license_id} license text against XML matcher"
