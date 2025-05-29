import click
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from .transformer import XMLToRegexTransformer
from .types import LicenseMatcher, Matcher
from .matcher import match


def pretty_print_result(result, indent=0):
    """Pretty print transformer results with proper formatting for dataclasses."""
    spaces = "  " * indent

    if isinstance(result, LicenseMatcher):
        click.echo(f"{spaces}LicenseMatcher (xpath: {result.xpath}):")
        if result.title is not None:
            click.echo(f"{spaces}  title:")
            pretty_print_result(result.title, indent + 2)
        if result.copyright is not None:
            click.echo(f"{spaces}  copyright:")
            pretty_print_result(result.copyright, indent + 2)
        if result.parts:
            click.echo(f"{spaces}  parts:")
            for i, part in enumerate(result.parts):
                click.echo(f"{spaces}    [{i}]:")
                pretty_print_result(part, indent + 3)
    elif isinstance(result, Matcher):
        click.echo(f"{spaces}{type(result).__name__} (xpath: {result.xpath}):")
        if result.parts:
            click.echo(f"{spaces}  parts:")
            for i, part in enumerate(result.parts):
                click.echo(f"{spaces}    [{i}]:")
                pretty_print_result(part, indent + 3)
    elif isinstance(result, str):
        # For strings, show them with quotes and handle long strings
        if len(result) > 80:
            click.echo(f'{spaces}"{result[:77]}..."')
        else:
            click.echo(f'{spaces}"{result}"')
    else:
        click.echo(f"{spaces}{result}")


@click.group()
def cli():
    """SPDX License Matcher CLI tool."""
    pass


@cli.command()
@click.argument("xml_file", type=click.Path(exists=True, path_type=Path))
def transform(xml_file):
    """Transform an XML license file using the SPDX transformer.

    Args:
        xml_file: Path to the XML license file to transform
        output_format: Format for displaying the result (pretty, json, or raw)
    """

    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Transform using our XMLToRegexTransformer
    transformer = XMLToRegexTransformer()
    result = transformer.transform(root)

    click.echo(f"Transformed {xml_file.name}:")
    click.echo("=" * 50)

    pretty_print_result(result)


@cli.command()
@click.argument("template_xml", type=click.Path(exists=True, path_type=Path))
@click.argument("license_file", type=click.Path(exists=True, path_type=Path))
@click.option("-v", "--verbose", count=True, help="Increase verbosity (use -v, -vv, or -vvv)")
def match_license(template_xml, license_file, verbose):
    """Match a license text against an SPDX template.
    
    Args:
        template_xml: Path to the SPDX template XML file
        license_file: Path to the license text file to match
        verbose: Verbosity level for logging
    """
    
    # Set up logging based on verbosity
    if verbose == 1:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    elif verbose == 2:
        logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(name)s: %(message)s')
    elif verbose >= 3:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    
    # Parse the template XML file
    tree = ET.parse(template_xml)
    root = tree.getroot()
    
    # Transform template to LicenseMatcher
    transformer = XMLToRegexTransformer()
    template_matcher = transformer.transform(root)
    
    if not isinstance(template_matcher, LicenseMatcher):
        click.echo("Error: Template XML did not produce a LicenseMatcher", err=True)
        return
    
    # Read the license text
    try:
        license_text = license_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            license_text = license_file.read_text(encoding='latin-1')
        except Exception as e:
            click.echo(f"Error reading license file: {e}", err=True)
            return
    
    # Apply the match function
    result = match(template_matcher, license_text)
    
    click.echo(f"Matching {license_file.name} against template {template_xml.name}:")
    click.echo("=" * 60)
    
    if result is None:
        click.echo("❌ NO MATCH - Some parts of the template were not found in the license text")
    else:
        click.echo("✅ MATCH - All template parts found in license text")
        if result.strip():
            click.echo(f"\nUnmatched text remaining ({len(result)} characters):")
            click.echo("-" * 40)
            click.echo(result[:500] + ("..." if len(result) > 500 else ""))
        else:
            click.echo("\n🎯 PERFECT MATCH - All text matched, no remainder")


if __name__ == "__main__":
    cli()
