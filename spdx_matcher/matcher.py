import re
import logging
from typing import Optional
from .types import LicenseMatcher, Matcher, TransformResult

logger = logging.getLogger(__name__)


def match(m: LicenseMatcher, text_to_match: str) -> Optional[str]:
    """
    Match a LicenseMatcher against text.

    Returns:
        None if there are parts in m that don't match the text
        The unmatched text if all parts of m are found in the text
    """
    logger.info(f"Starting match with LicenseMatcher (xpath: {m.xpath})")
    logger.debug(f"Input text length: {len(text_to_match)} characters")

    remaining_text = text_to_match

    # Check title if present
    if m.title is not None:
        logger.info("Matching title...")
        title_result = _match_transform_result(m.title, remaining_text)
        if title_result is not None:
            logger.info("Title matched successfully")
            remaining_text = title_result
        else:
            logger.warning("Title failed to match")

    # Check copyright if present
    if m.copyright is not None:
        logger.info("Matching copyright...")
        copyright_result = _match_transform_result(m.copyright, remaining_text)
        if copyright_result is None:
            logger.error("Copyright failed to match")
            return None
        logger.info("Copyright matched successfully")
        remaining_text = copyright_result

    # Check all parts
    logger.info(f"Matching {len(m.parts)} parts...")
    for i, part in enumerate(m.parts):
        logger.info(f"Matching part {i+1}/{len(m.parts)}")
        part_result = _match_transform_result(part, remaining_text)
        if part_result is None:
            logger.error(f"Part {i+1} failed to match")
            return None
        logger.info(f"Part {i+1} matched successfully")
        remaining_text = part_result

    logger.info(f"All parts matched. Remaining text: {len(remaining_text)} characters")
    return remaining_text


def _match_transform_result(transform_result: TransformResult, text: str) -> Optional[str]:
    """
    Match a TransformResult against text and return remaining text.

    Returns:
        None if the transform_result doesn't match
        The remaining text after removing the matched portion
    """
    if isinstance(transform_result, str):
        logger.debug(f"Matching string pattern:\n\t{transform_result!r}")
        logger.debug(f"Against text\n\t{text!r}")

        # For string patterns, try to match as regex

        pattern = re.compile(transform_result, re.IGNORECASE | re.DOTALL)
        match = pattern.search(text)
        if match:
            logger.debug(f"Regex match found at position {match.span()}")
            logger.debug(f"Matched text:\n\t{match.group(0)!r}")
            # Remove the matched text and return the remainder
            start, end = match.span()
            return text[:start] + text[end:]
        else:
            logger.debug("Regex pattern did not match")
            return None

    elif isinstance(transform_result, Matcher):
        logger.debug(
            f"Matching {type(transform_result).__name__} with {len(transform_result.parts)} parts (xpath: {transform_result.xpath})"
        )
        # For Matcher objects, check all parts
        remaining_text = text
        for i, part in enumerate(transform_result.parts):
            logger.debug(f"Matching sub-part {i+1}/{len(transform_result.parts)}")
            part_result = _match_transform_result(part, remaining_text)
            if part_result is None:
                logger.debug(f"Sub-part {i+1} failed to match")
                return None
            remaining_text = part_result
        logger.debug(f"All {len(transform_result.parts)} sub-parts matched")
        return remaining_text

    else:
        logger.warning(f"Unknown transform result type: {type(transform_result)}")
        # Unknown type, consider it a non-match
        return None
