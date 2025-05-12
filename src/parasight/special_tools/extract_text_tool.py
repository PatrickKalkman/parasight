from typing import Any, Dict, Optional

from agents import function_tool


@function_tool
def extract_text_from_elements(parsed_data: Dict[str, Any], element_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract text from elements in OmniParser results, optionally filtered by type.

    Args:
        parsed_data: The parsed data from OmniParser
        element_type: Optional filter for element type

    Returns:
        Dictionary with extracted text from elements
    """
    if not parsed_data.get("success", False):
        return {"success": False, "error": parsed_data.get("error", "Invalid parsed data")}

    parsed_content_list = parsed_data.get("data", {}).get("parsed_content_list", [])
    if not parsed_content_list:
        return {"success": False, "error": "No elements found in parsed data"}

    extracted_text = []

    for element in parsed_content_list:
        # Skip elements that don't match the requested type
        if element_type and element.get("element_type") != element_type:
            continue

        text = element.get("text", "").strip()
        if text:
            extracted_text.append({
                "text": text,
                "position": {"x": element.get("center_x"), "y": element.get("center_y")},
                "element_type": element.get("element_type", "unknown"),
            })

    return {"success": True, "element_count": len(extracted_text), "extracted_text": extracted_text}
