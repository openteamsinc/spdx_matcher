import xml.etree.ElementTree as ET
import re
from typing import Optional


def normalize(text: str) -> str:
    """
    Normalize text for license matching.

    Args:
        text: The text to normalize

    Returns:
        Normalized text: lowercase, single spaces, no newlines
    """
    # Convert to lowercase
    normalized = text.lower()

    # Replace all whitespace (including newlines) with single spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Strip leading/trailing whitespace
    normalized = normalized.strip()

    return normalized


def make_regex(elem: ET.Element) -> str:
    """
    Create a regex pattern from an XML element.

    Args:
        elem: The XML element to create regex from

    Returns:
        Regex pattern string
    """
    if elem.tag.endswith("}alt"):
        # For <alt> elements, use the match attribute if present
        match_pattern = elem.get("match", "")
        if match_pattern:
            return match_pattern
        # Otherwise, escape the element text
        text = elem.text or ""
        return re.escape(text)

    elif elem.tag.endswith("}optional"):
        # For <optional> elements, make the content optional
        text = "".join(elem.itertext())
        escaped_text = re.escape(text)
        return f"({escaped_text})?"

    else:
        # For regular elements, escape the text content
        text = "".join(elem.itertext())
        return re.escape(text)


def match_list_item(item_elem: ET.Element, license_text: str) -> Optional[str]:
    """
    Match a list item element against license text and return the text with matched part removed.

    Args:
        item_elem: The item XML element to match
        license_text: The license text to match against

    Returns:
        License text with the matched portion removed, or None if no match found
    """
    # Build regex pattern from the item element
    pattern_parts = []

    # Handle bullet if present
    ns = "{http://www.spdx.org/license}"
    bullet_elem = item_elem.find(f"{ns}bullet")
    if bullet_elem is not None:
        bullet_text = bullet_elem.text or ""
        if bullet_text.strip():
            # Make bullet flexible - could be "1.", "1)", "(1)", etc.
            bullet_pattern = re.escape(bullet_text.strip())
            pattern_parts.append(bullet_pattern)

    # Handle text before first child
    if item_elem.text:
        normalized_text = normalize(item_elem.text)
        if normalized_text:
            pattern_parts.append(re.escape(normalized_text))

    # Process child elements (excluding bullet)
    for child in item_elem:
        if child.tag.endswith("}bullet"):
            # Already handled above
            pass
        elif child.tag.endswith("}alt"):
            # For alt elements, wrap the pattern in parentheses
            alt_pattern = child.get("match", "")
            if alt_pattern:
                pattern_parts.append(f"({alt_pattern})")
            else:
                # Use the element text if no match pattern
                alt_text = normalize(child.text or "")
                if alt_text:
                    pattern_parts.append(re.escape(alt_text))
        elif child.tag.endswith("}optional"):
            # For optional elements, make them optional with ?
            optional_text = normalize("".join(child.itertext()))
            if optional_text:
                pattern_parts.append(f"({re.escape(optional_text)})?")
        else:
            # For other elements, escape the text
            elem_text = normalize("".join(child.itertext()))
            if elem_text:
                pattern_parts.append(re.escape(elem_text))

        # Handle tail text after child
        if child.tail:
            normalized_tail = normalize(child.tail)
            if normalized_tail:
                pattern_parts.append(re.escape(normalized_tail))

    # Join pattern parts with flexible whitespace matching
    pattern_with_flexible_space = []
    for part in filter(None, pattern_parts):
        # Replace escaped spaces with flexible whitespace pattern
        flexible_part = part.replace(r"\ ", r"\s+")
        pattern_with_flexible_space.append(flexible_part)

    full_pattern = r"\s*".join(pattern_with_flexible_space)

    # Try to find and remove the match
    match = re.search(full_pattern, license_text, re.IGNORECASE | re.DOTALL)
    if match:
        # Remove the matched text
        return license_text.replace(match.group(0), "", 1)

    # If no match found, return None
    return None


def match_list(list_elem: ET.Element, license_text: str) -> Optional[str]:
    """
    Match a list element against license text and return the text with matched part removed.

    Args:
        list_elem: The list XML element to match
        license_text: The license text to match against

    Returns:
        License text with the matched portion removed, or None if any item failed to match
    """
    current_text = license_text
    ns = "{http://www.spdx.org/license}"

    # Process each item in the list
    for item_elem in list_elem.findall(f"{ns}item"):
        new_text = match_list_item(item_elem, current_text)
        if new_text is None:
            # If any item fails to match, the whole list fails
            return None
        current_text = new_text

    return current_text


def match_copyright(copyright_elem: ET.Element, license_text: str) -> str:
    """
    Match a copyrightText element against license text and return the text with matched part removed.

    Copyright text is optional and may be multiple lines and/or multiple copyrights.
    It may also end with "All rights reserved".

    Args:
        copyright_elem: The copyrightText XML element to match
        license_text: The license text to match against

    Returns:
        License text with the matched portion removed, or original text if no match
    """
    # Get the paragraph inside copyrightText
    ns = "{http://www.spdx.org/license}"
    p_elem = copyright_elem.find(f"{ns}p")

    if p_elem is None:
        return license_text

    # Get the copyright text from the paragraph
    copyright_text = "".join(p_elem.itertext()).strip()
    if not copyright_text:
        return license_text

    # Split license text into lines
    lines = license_text.split("\n")

    # Look for copyright declaration lines - only lines that START with copyright symbols
    lines_to_remove = []

    for i, line in enumerate(lines):
        normalized_line = normalize(line)

        # Only match lines that start with copyright declarations
        if (
            normalized_line.startswith("copyright")
            or normalized_line.startswith("(c)")
            or normalized_line.startswith("©")
        ):
            lines_to_remove.append(i)
        # Also check for "All rights reserved" which often follows copyright
        elif "all rights reserved" in normalized_line and lines_to_remove:
            lines_to_remove.append(i)

    # Remove the identified copyright lines
    if lines_to_remove:
        remaining_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]
        return "\n".join(remaining_lines)

    # If no copyright lines found, return original text
    return license_text


def match_title_text(title_elem: ET.Element, license_text: str) -> str:
    """
    Match a titleText element against license text and return the text with matched part removed.

    This is a special case of match_p that handles title text which should be a single line
    and can have text prefix and/or suffix in the title.

    Args:
        title_elem: The titleText XML element to match
        license_text: The license text to match against

    Returns:
        License text with the matched portion removed, or original text if no match
    """
    # Get the paragraph inside titleText
    ns = "{http://www.spdx.org/license}"
    p_elem = title_elem.find(f"{ns}p")

    if p_elem is None:
        return license_text

    # Get the title text from the paragraph
    title_text = "".join(p_elem.itertext()).strip()
    if not title_text:
        return license_text

    # Normalize the title text for matching
    normalized_title = normalize(title_text)

    # Split license text into lines and look for the title
    lines = license_text.split("\n")

    for i, line in enumerate(lines):
        normalized_line = normalize(line)

        # Check if the title appears anywhere in this line
        if normalized_title in normalized_line:
            # Remove this line from the license text
            remaining_lines = lines[:i] + lines[i + 1 :]
            return "\n".join(remaining_lines)

    # If no match found, return original text
    return license_text


def match_p(p_elem: ET.Element, license_text: str) -> Optional[str]:
    """
    Match a paragraph element against license text and return the text with matched part removed.

    Args:
        p_elem: The paragraph XML element to match
        license_text: The license text to match against

    Returns:
        License text with the matched portion removed, or None if no match found
    """
    # Build regex pattern from the paragraph element
    pattern_parts = []

    # Handle text before first child
    if p_elem.text:
        normalized_text = normalize(p_elem.text)
        if normalized_text:
            pattern_parts.append(re.escape(normalized_text))

    # Process child elements
    for child in p_elem:
        if child.tag.endswith("}alt"):
            # For alt elements, wrap the pattern in parentheses
            alt_pattern = child.get("match", "")
            if alt_pattern:
                pattern_parts.append(f"({alt_pattern})")
            else:
                # Use the element text if no match pattern
                alt_text = normalize(child.text or "")
                if alt_text:
                    pattern_parts.append(re.escape(alt_text))
        elif child.tag.endswith("}optional"):
            # For optional elements, make them optional with ?
            optional_text = normalize("".join(child.itertext()))
            if optional_text:
                pattern_parts.append(f"({re.escape(optional_text)})?")
        else:
            # For other elements, escape the text
            elem_text = normalize("".join(child.itertext()))
            if elem_text:
                pattern_parts.append(re.escape(elem_text))

        # Handle tail text after child
        if child.tail:
            normalized_tail = normalize(child.tail)
            if normalized_tail:
                pattern_parts.append(re.escape(normalized_tail))

    # Join pattern parts with flexible whitespace matching
    # Replace escaped spaces with \s+ for flexible whitespace matching
    pattern_with_flexible_space = []
    for part in filter(None, pattern_parts):
        # Replace escaped spaces with flexible whitespace pattern
        flexible_part = part.replace(r"\ ", r"\s+")
        pattern_with_flexible_space.append(flexible_part)

    full_pattern = r"\s*".join(pattern_with_flexible_space)
    print(f"Pattern: {repr(full_pattern)}")
    print(f"Text to match: {repr(license_text[:100])}")

    # Try to find and remove the match
    match = re.search(full_pattern, license_text, re.IGNORECASE)
    if match:
        print(f"Match found: {repr(match.group(0))}")
        # Remove the matched text
        return license_text.replace(match.group(0), "", 1)

    print("No match found")
    # If no match found, return None
    return None
