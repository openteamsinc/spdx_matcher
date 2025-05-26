import os
from spdx_matcher.license_loader import load_licenses


def test_load_licenses():
    """
    Test the license loading functionality.
    """
    # Get path to license directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    license_dir = os.path.join(project_root, "license-list-XML", "src")

    # Load licenses
    licenses = load_licenses(license_dir)
    print(f"Loaded {len(licenses)} licenses")

    # Print some example license data
    if licenses:
        sample_license_id = next(iter(licenses))
        print(f"\nSample license: {sample_license_id}")
        sample_license = licenses[sample_license_id]
        print(f"Name: {sample_license['name']}")
        print(f"OSI Approved: {sample_license['is_osi_approved']}")
        if "notes" in sample_license:
            print(f"Notes: {sample_license['notes']}")
        print(f"Cross references: {', '.join(sample_license['cross_refs'])}")

    # Ensure we loaded at least some licenses
    assert len(licenses) > 0, "No licenses were loaded"

    # Test a few known licenses
    known_licenses = ["MIT", "Apache-2.0", "GPL-3.0-only"]
    for license_id in known_licenses:
        if license_id in licenses:
            print(f"Found {license_id}: {licenses[license_id]['name']}")
        else:
            print(f"Warning: {license_id} not found in loaded licenses")


if __name__ == "__main__":
    test_load_licenses()
