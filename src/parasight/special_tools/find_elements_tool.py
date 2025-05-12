from typing import Any, Dict, Literal

from agents import function_tool


@function_tool
def find_elements_by_description(
    parsed_data: Dict[str, Any],
    description: str,
    match_type: Literal["contains", "exact", "startswith", "endswith"] = "contains",
    case_sensitive: bool = False,
    max_results: int = 5,
) -> Dict[str, Any]:
    """
    Find elements in OmniParser results that match a description.

    Args:
        parsed_data: The parsed data from OmniParser
        description: Description of the element to find
        match_type: How to match the description to element text
        case_sensitive: Whether matching should be case-sensitive
        max_results: Maximum number of matching elements to return

    Returns:
        Dictionary with matching elements
    """
    if not parsed_data.get("success", False):
        return {"success": False, "error": parsed_data.get("error", "Invalid parsed data")}

    parsed_content_list = parsed_data.get("data", {}).get("parsed_content_list", [])
    if not parsed_content_list:
        return {"success": False, "error": "No elements found in parsed data"}

    matching_elements = []

    # Adjust description based on case sensitivity
    search_description = description if case_sensitive else description.lower()

    for element in parsed_content_list:
        element_text = element.get("text", "")

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
            matching_elements.append({
                "element": element,
                "position": {"x": element.get("center_x"), "y": element.get("center_y")},
                "text": element_text,
                "element_type": element.get("element_type", "unknown"),
            })

            if len(matching_elements) >= max_results:
                break

    return {"success": True, "matches_found": len(matching_elements), "matching_elements": matching_elements}
