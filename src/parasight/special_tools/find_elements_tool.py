from typing import List, Literal, Optional  # Added List, Optional

from agents import function_tool
from pydantic import BaseModel

# Import models and helpers from extract_text_tool
from .extract_text_tool import (
    OmniParserElement,
    OmniParserResultInput,
    Position,
    _parse_coordinates,
    _parse_element_line,
)


# --- Pydantic Models for find_elements_by_description output ---
class MatchingElementOutput(BaseModel):
    element: OmniParserElement  # Re-use OmniParserElement
    position: Position  # Re-use Position
    text: str
    element_type: str


class FindElementsResultOutput(BaseModel):
    success: bool
    matches_found: Optional[int] = None
    matching_elements: Optional[List[MatchingElementOutput]] = None
    error: Optional[str] = None


# --- End Pydantic Models ---


# Core logic function (without decorator)
def _find_elements_by_description_core(
    parsed_data: OmniParserResultInput,  # Use OmniParserResultInput
    description: str,
    match_type: Literal["contains", "exact", "startswith", "endswith"],
) -> FindElementsResultOutput:
    """
    Find elements in OmniParser results that match a description.

    Args:
        parsed_data: The parsed data from OmniParser
        description: Description of the element to find
        match_type: How to match the description to element text (contains, exact, startswith, endswith)
        case_sensitive: Whether matching should be case-sensitive
        max_results: Maximum number of matching elements to return

    Returns:
        Pydantic model instance with matching elements
    """
    case_sensitive = False
    max_results = 5

    if not parsed_data.success:
        return FindElementsResultOutput(success=False, error=parsed_data.error or "Invalid parsed data")

    if not parsed_data.data or not parsed_data.data.parsed_content_list or not parsed_data.data.label_coordinates:
        return FindElementsResultOutput(success=False, error="Missing parsed content or coordinates in OmniParser data")

    # Parse coordinates
    coordinates = _parse_coordinates(parsed_data.data.label_coordinates)
    # Warning or error if coordinates couldn't be parsed? For now, proceed without positions if necessary.

    output_matching_elements: List[MatchingElementOutput] = []
    lines = parsed_data.data.parsed_content_list.strip().split("\n")

    # Adjust description based on case sensitivity
    search_description = description if case_sensitive else description.lower()

    for line in lines:
        parsed_line = _parse_element_line(line)
        if not parsed_line:
            continue  # Skip lines that don't match the expected format

        element_type_parsed, element_id_parsed, text_parsed = parsed_line

        # Adjust element text based on case sensitivity
        search_text = text_parsed if case_sensitive else text_parsed.lower()

        is_match = False
        if match_type == "contains":
            is_match = search_description in search_text
        elif match_type == "exact":
            is_match = search_description == search_text
        elif match_type == "startswith":
            is_match = search_text.startswith(search_description)
        elif match_type == "endswith":
            is_match = search_text.endswith(search_description)

        if is_match:
            # Get coordinates using the parsed ID
            coords = coordinates.get(element_id_parsed)
            center_x, center_y = (coords[0], coords[1]) if coords and len(coords) >= 2 else (None, None)

            # Create a simple OmniParserElement for the output
            # Note: We don't have the full element details here, just text, type, and position
            element_data = OmniParserElement(
                text=text_parsed,
                center_x=center_x,
                center_y=center_y,
                element_type=element_type_parsed,
            )

            output_matching_elements.append(
                MatchingElementOutput(
                    element=element_data,
                    position=Position(x=center_x, y=center_y),
                    text=text_parsed,  # Use the original case text
                    element_type=element_type_parsed,
                )
            )

            if len(output_matching_elements) >= max_results:
                break

    return FindElementsResultOutput(
        success=True, matches_found=len(output_matching_elements), matching_elements=output_matching_elements
    )


# Apply the function_tool decorator to the core logic function
find_elements_by_description = function_tool(_find_elements_by_description_core)
