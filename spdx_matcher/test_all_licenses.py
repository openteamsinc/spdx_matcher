"""
Test license XML to text matching for all available licenses.
"""

import pytest
import os
import xml.etree.ElementTree as ET
from .transformer import XMLToRegexTransformer
from .matcher import match


class TestAllLicenses:
    """Test license XML to text matching per SPDX guidelines."""

    @pytest.mark.parametrize(
        "license_id",
        [
            "BSD-2-Clause",
            "MIT", 
            "Apache-2.0",
            "GPL-3.0-only",
            "LGPL-2.1-only",
            "0BSD",
            "BSD-3-Clause",
            "ISC",
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
        with open(xml_path) as f:
            tree = ET.parse(f)
        root = tree.getroot()
        
        # Load text content
        with open(txt_path) as f:
            license_text = f.read()
            
        # Transform XML to matcher
        transformer = XMLToRegexTransformer()
        ns = "{http://www.spdx.org/license}"
        
        # Find the license element
        license_elem = root.find(f".//{ns}license")
        if license_elem is None:
            pytest.fail(f"No license element found in {license_id} XML")
            
        # Transform the license element to a matcher
        license_matcher = transformer.transform(license_elem)
        
        # Test that the matcher can match the license text
        if hasattr(license_matcher, 'parts'):
            # If it's a matcher object, test using the match function
            result = match(license_matcher, license_text)
            assert result is not None, f"Failed to match {license_id} license text against XML matcher"
        else:
            # If it's a string pattern, test as regex
            import re
            pattern = re.compile(str(license_matcher), re.IGNORECASE | re.DOTALL)
            match_result = pattern.search(license_text)
            assert match_result is not None, f"Failed to match {license_id} license text against regex pattern"