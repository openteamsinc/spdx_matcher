import xml.etree.ElementTree as ET
from typing import Optional
from spdx_matcher.matcher import match_p, match_title_text, match_copyright, match_list
import logging

log = logging.getLogger(__name__)


def strip_matches(root: ET.Element, license_to_match: str) -> Optional[str]:
    """
    Processes XML license template and matches against input text.

    Args:
        root: The root XML element of the license template
        license_to_match: The license text to match against

    Returns:
        The unmatched text as a string, or None if any element failed to match
    """
    ns = "{http://www.spdx.org/license}"
    text_elem = root.find(f".//{ns}text")

    if text_elem is None:
        return None

    current_text = license_to_match

    # Check if there's implicit text content (text directly in <text> element)
    implicit_text = text_elem.text
    if implicit_text and implicit_text.strip():
        # Create an implicit paragraph element for the direct text content
        implicit_p = ET.Element("{http://www.spdx.org/license}p")
        implicit_p.text = implicit_text.strip()

        # Process the implicit paragraph
        result = _process_single_element(implicit_p, current_text, is_optional=False)
        if result is None:
            log.debug(f"Failed to match implicit text: {implicit_text.strip()[:100]}...")
            return None
        current_text = result

    # Process each child element in the text section
    for elem in text_elem:
        if elem.tag.endswith("}optional"):
            # Process optional elements - try to match but don't fail if they don't match
            optional_result = _process_element_children(elem, current_text, is_optional=True)
            if optional_result is not None:
                before_match = current_text
                current_text = optional_result
                log.debug(
                    f"Optional element match - before length: {len(before_match)}, after length: {len(current_text)}"
                )
            else:
                log.debug(f"Optional element not matched (skipping): {ET.tostring(elem, encoding='unicode')[:100]}...")

        else:
            # Process non-optional elements - must match or fail
            result = _process_single_element(elem, current_text, is_optional=False)
            if result is None:
                return None
            current_text = result

        # Also handle any tail text after this element
        tail_text = elem.tail
        if tail_text and tail_text.strip():
            # Create an implicit paragraph element for the tail text
            implicit_tail_p = ET.Element("{http://www.spdx.org/license}p")
            implicit_tail_p.text = tail_text.strip()

            # Process the implicit tail paragraph
            result = _process_single_element(implicit_tail_p, current_text, is_optional=False)
            if result is None:
                log.debug(f"Failed to match tail text: {tail_text.strip()[:100]}...")
                return None
            current_text = result

    # Return the remaining unmatched text
    return current_text.strip()


def _process_single_element(elem: ET.Element, text: str, is_optional: bool = False) -> Optional[str]:
    """
    Process a single XML element and match it against the text.

    Args:
        elem: The XML element to process
        text: The current license text to match against
        is_optional: Whether this element is within an optional context

    Returns:
        The updated text with matched content removed, or None if match failed
    """
    if elem.tag.endswith("}p"):
        # Process paragraph elements using match_p
        new_text = match_p(elem, text)
        if new_text is None:
            if not is_optional:
                log.debug(f"Failed to match paragraph: {ET.tostring(elem, encoding='unicode')[:100]}...")
            return None

        before_match = text
        log.debug(f"Paragraph match - before length: {len(before_match)}, after length: {len(new_text)}")
        return new_text

    elif elem.tag.endswith("}titleText"):
        # Process titleText elements using match_title_text
        before_match = text
        result = match_title_text(elem, text)
        log.debug(f"Title text match - before length: {len(before_match)}, after length: {len(result)}")
        return result

    elif elem.tag.endswith("}copyrightText"):
        # Process copyrightText elements using match_copyright
        before_match = text
        result = match_copyright(elem, text)
        log.debug(f"Copyright match - before length: {len(before_match)}, after length: {len(result)}")
        return result

    elif elem.tag.endswith("}list"):
        # Process list elements using match_list
        new_text = match_list(elem, text)
        if new_text is None:
            if not is_optional:
                log.debug(f"Failed to match list: {ET.tostring(elem, encoding='unicode')[:100]}...")
            return None

        before_match = text
        log.debug(f"List match - before length: {len(before_match)}, after length: {len(new_text)}")
        return new_text

    elif elem.tag.endswith("}alt"):
        # Process alt elements as if they were wrapped in a paragraph
        # Create an implicit paragraph element containing the alt element
        implicit_p = ET.Element("{http://www.spdx.org/license}p")
        implicit_p.append(elem)
        
        # Process the implicit paragraph
        new_text = match_p(implicit_p, text)
        if new_text is None:
            if not is_optional:
                log.debug(f"Failed to match alt element: {ET.tostring(elem, encoding='unicode')[:100]}...")
            return None

        before_match = text
        log.debug(f"Alt element match - before length: {len(before_match)}, after length: {len(new_text)}")
        return new_text

    else:
        if is_optional:
            # For unknown element types in optional context, we'll be permissive
            log.debug(f"Skipping unknown element type in optional context: {elem.tag}")
            return text  # Return unchanged text
        else:
            raise ValueError(f"Unexpected element type: {elem.tag}")


def _process_element_children(parent_elem: ET.Element, text: str, is_optional: bool = False) -> Optional[str]:
    """
    Process all child elements within a parent element (like <optional>).

    Args:
        parent_elem: The parent XML element containing child elements
        text: The current license text to match against
        is_optional: Whether this is processing within an optional context

    Returns:
        The updated text with matched content removed, or None if any child failed to match
    """
    current_text = text

    # Process each child element
    for child in parent_elem:
        result = _process_single_element(child, current_text, is_optional=is_optional)
        if result is None:
            return None
        current_text = result

    return current_text
