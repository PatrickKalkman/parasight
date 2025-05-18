import base64
import os
from typing import Any, Dict

from agents import function_tool

from parasight.special_tools.analyze_image_with_omniparser_tool import _analyze_image_with_omniparser_core

# Import Pydantic models used by the tools
from parasight.special_tools.extract_text_tool import OmniParserResultInput  # Import the input model
from parasight.special_tools.find_elements_tool import FindElementsResultOutput, _find_elements_by_description_core


# Core logic function (without decorator)
async def _validate_element_exists_core(image_path: str, element_description: str) -> Dict[str, Any]:
    """
    Validate if an element exists on a given image.

    Args:
        image_path: Path to the image file to analyze. This path is typically obtained from other tools like `take_screenshot` or `interact_with_element_sequence`.
        element_description: Description of the element to find.

    Returns:
        Validation result with element details if found.
    """

    # All subsequent operations are wrapped in a try.
    try:
        # Check if the image file exists
        if not os.path.exists(image_path):
            return {"success": False, "error": f"Image file not found at path: {image_path}"}

        try:
            # Analyze the image with OmniParser using the file path
            analysis_result = await _analyze_image_with_omniparser_core(
                image_path=image_path, box_threshold=0.05, iou_threshold=0.1
            )
        except Exception as e:
            return {"success": False, "error": f"OmniParser analysis failed unexpectedly: {e}"}

        if not analysis_result.get("success", False):
            return {"success": False, "error": analysis_result.get("error", "Failed to analyze image")}

        # Convert the analysis_result dict to the Pydantic model
        try:
            parsed_data_input = OmniParserResultInput(**analysis_result)
        except Exception as e:
            # Handle potential validation errors during model creation
            return {"success": False, "error": f"Failed to parse analysis result: {e}"}

        # Find matching elements (returns FindElementsResultOutput model)
        find_result: FindElementsResultOutput = _find_elements_by_description_core(
            parsed_data=parsed_data_input, description=element_description, match_type="contains"
        )

        if not find_result.success:
            return {"success": False, "error": find_result.error or "Failed to find elements"}

        # Check if any matching elements were found
        matches_found = find_result.matches_found or 0
        if matches_found > 0:
            return {
                "success": True,
                "element_exists": True,
                "matches_found": matches_found,
                # Convert Pydantic models to dicts for the final JSON-like output if needed,
                # or define a Pydantic model for this tool's output as well.
                "matching_elements": [elem.model_dump() for elem in find_result.matching_elements]
                if find_result.matching_elements
                else [],
            }
        else:
            return {
                "success": True,
                "element_exists": False,
                "error": f"No elements matching '{element_description}' found on the page",
            }
    except Exception as e:
        # Catch any other unexpected errors during the process
        return {"success": False, "error": f"An unexpected error occurred: {e}"}


# Apply the function_tool decorator to the core logic function
validate_element_exists = function_tool(_validate_element_exists_core)
