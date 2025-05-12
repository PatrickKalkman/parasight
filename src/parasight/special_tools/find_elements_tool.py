from typing import List, Literal, Optional  # Added List, Optional

from agents import function_tool
from pydantic import BaseModel

# Import models from extract_text_tool
from .extract_text_tool import OmniParserElement, OmniParserResultInput, Position


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


@function_tool
def find_elements_by_description(
    parsed_data: OmniParserResultInput,  # Use OmniParserResultInput
    description: str,
    match_type: Literal["contains", "exact", "startswith", "endswith"] = "contains",
    case_sensitive: bool = False,
    max_results: int = 5,
) -> FindElementsResultOutput:  # Use FindElementsResultOutput
    """
    Find elements in OmniParser results that match a description.

    Args:
        parsed_data: The parsed data from OmniParser
        description: Description of the element to find
        match_type: How to match the description to element text
        case_sensitive: Whether matching should be case-sensitive
        max_results: Maximum number of matching elements to return

    Returns:
        Pydantic model instance with matching elements
    """
    if not parsed_data.success:
        return FindElementsResultOutput(success=False, error=parsed_data.error or "Invalid parsed data")

    if not parsed_data.data or not parsed_data.data.parsed_content_list:
        return FindElementsResultOutput(success=False, error="No elements found in parsed data")

    output_matching_elements: List[MatchingElementOutput] = []

    # Adjust description based on case sensitivity
    search_description = description if case_sensitive else description.lower()

    for element_model in parsed_data.data.parsed_content_list:  # Iterate over OmniParserElement models
        element_text = element_model.text or ""

        # Adjust element text based on case sensitivity
        search_text = element_text if case_sensitive else element_text.lower()

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
            output_matching_elements.append(
                MatchingElementOutput(
                    element=element_model,  # Pass the Pydantic model instance
                    position=Position(x=element_model.center_x, y=element_model.center_y),
                    text=element_text,
                    element_type=element_model.element_type or "unknown",
                )
            )

            if len(output_matching_elements) >= max_results:
                break

    return FindElementsResultOutput(
        success=True, matches_found=len(output_matching_elements), matching_elements=output_matching_elements
    )
