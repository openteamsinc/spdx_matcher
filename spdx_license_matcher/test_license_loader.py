from spdx_license_matcher.license_loader import load_licenses


def test_load_licenses():
    """
    Test the license loading functionality.
    """
    # Get path to license directory

    # Load licenses
    licenses = load_licenses()
    assert len(licenses) > 0
