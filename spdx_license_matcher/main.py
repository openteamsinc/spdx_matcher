import logging
import sys
import textwrap
from pathlib import Path
from pprint import pprint

import click
from lxml import etree

from .find import find_license
from .matchers import LicenseMatcher, LicenseResult
from .normalize import normalize as normalize_fn
from .transformer import XMLToRegexTransformer


def pretty_print_result(result, indent=0):
    """Pretty print transformer results with proper formatting for dataclasses."""
    pprint(result.to_dict())


@click.group()
@click.option("-v", "--verbose", count=True, help="Increase verbosity (use -v, -vv, or -vvv)")
def cli(verbose):
    """SPDX License Matcher CLI tool."""
    # Set up logging based on verbosity
    if verbose == 1:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    elif verbose == 2:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(name)s: %(message)s")
    elif verbose >= 3:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


@cli.command()
@click.argument("xml_file", type=click.Path(exists=True, path_type=Path))
def transform(xml_file):
    """Transform an XML license file using the SPDX transformer.

    Args:
        xml_file: Path to the XML license file to transform
        output_format: Format for displaying the result (pretty, json, or raw)
    """

    # Parse the XML file
    with open(xml_file, "rb") as fd:
        xml_str = fd.read()
    root = etree.fromstring(xml_str)

    # Transform using our XMLToRegexTransformer
    transformer = XMLToRegexTransformer()
    result = transformer.transform(root)
    click.echo(f"Transformed {xml_file.name}:")
    click.echo("=" * 50)

    pretty_print_result(result)


@cli.command()
@click.argument("license_file", type=click.Path(exists=True, path_type=Path))
def normalize(license_file):
    with open(license_file) as fd:
        data = fd.read()
    print(normalize_fn(data))


@cli.command()
@click.argument("template_xml", type=click.Path(exists=True, path_type=Path))
@click.argument("license_file", type=click.Path(exists=True, path_type=Path))
def match(template_xml, license_file):
    """Match a license text against an SPDX template.

    Args:
        template_xml: Path to the SPDX template XML file
        license_file: Path to the license text file to match
    """

    with open(template_xml, "rb") as fd:
        xml_str = fd.read()

    root = etree.fromstring(xml_str)

    # Transform template to LicenseMatcher
    transformer = XMLToRegexTransformer()
    template_matcher = transformer.transform(root)

    if not isinstance(template_matcher, LicenseMatcher):
        click.echo("Error: Template XML did not produce a LicenseMatcher", err=True)
        return

    # Read the license text
    try:
        license_text = license_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            license_text = license_file.read_text(encoding="latin-1")
        except Exception as e:
            click.echo(f"Error reading license file: {e}", err=True)
            return

    normalized_license_text = normalize_fn(license_text)
    result = LicenseResult(normalized_license_text)

    click.echo(f"Matching {license_file.name} against template {template_xml.name}:")
    click.echo("=" * 60)

    template_matcher.match(result)

    remaining_text = result.text.strip()
    if remaining_text:
        click.echo("Remaining text after matching:")
        click.echo("-" * 40)
        click.echo(result.text)
    else:
        click.echo("🎯 PERFECT MATCH - All text matched, no remainder")


@cli.command()
@click.argument("license_file", type=click.Path(exists=True, path_type=Path))
@click.option("--best", is_flag=True, help="Stop after finding the best match")
def find(license_file: str, best=False) -> None:

    with open(license_file) as fd:
        license_text = fd.read()
    licenses = find_license(license_text)
    if len(licenses) == 0:
        click.echo("No matching licenses found.", err=True)
        sys.exit(1)

    for i, data in enumerate(licenses):
        name = data["name"]
        spdx_id = data["spdx_id"]
        extra_characters: str = data["extra_characters"]
        restrictions = data["restrictions"]
        kind = data["kind"]

        click.echo(f"{'✅' if i==0 else ''} Found license: {spdx_id!r}")
        click.echo(f"  Name: {name} ({kind})")
        if restrictions:
            click.echo(f"  Restrictions: {', '.join(restrictions)}")
        else:
            click.echo("  No restrictions")
        if len(extra_characters) > 0:
            click.echo("  Extra characters:")
            click.echo(textwrap.indent(extra_characters, "| "))

        else:
            click.echo("🎯 Perfect match with no extra characters")

        if best:
            return


if __name__ == "__main__":
    cli()
if __name__ == "__main__":
    cli()
