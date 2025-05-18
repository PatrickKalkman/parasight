from typing import Any, Dict

import base64
import os
from typing import Any, Dict

from agents import function_tool

from parasight.special_tools.analyze_image_with_omniparser_tool import _analyze_image_with_omniparser_core

# Import Pydantic models used by the tools
from parasight.special_tools.extract_text_tool import OmniParserResultInput  # Import the input model
from parasight.special_tools.find_elements_tool import FindElementsResultOutput, _find_elements_by_description_core


# Core logic function (without decorator)
async def _validate_element_exists_core(base64_image_string: str, element_description: str) -> Dict[str, Any]:
    """
    Validate if an element exists on a given image.

    Args:
        base64_image_string: Base64 encoded string of the image to analyze.
        element_description: Description of the element to find

    Returns:
        Validation result with element details if found
    """

    screenshot_file_path = "temp_validation_image.png"  # Path for the temporary image

    try:
        # Decode the base64 string and save it as an image file
        image_data = base64.b64decode(base64_image_string)
        with open(screenshot_file_path, "wb") as f:
            f.write(image_data)
    except Exception as e:
        # If decoding or file writing fails, return an error
        return {"success": False, "error": f"Failed to decode or save image: {e}"}

    # All subsequent operations are wrapped in a try to ensure finally is always called for cleanup,
    # assuming the initial file creation was successful.
    try:
        try:
            # Analyze the image with OmniParser using the file path
            analysis_result = await _analyze_image_with_omniparser_core(
                image_path=screenshot_file_path, box_threshold=0.05, iou_threshold=0.1
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
    finally:
        # Clean up the temporary image file
        if os.path.exists(screenshot_file_path):
            try:
                os.remove(screenshot_file_path)
            except Exception as e:
                # Log or handle cleanup error if necessary, but don't let it overshadow the main result
                # Consider using logger for production code instead of print
                print(f"Error deleting temporary file {screenshot_file_path}: {e}")


# Apply the function_tool decorator to the core logic function
validate_element_exists = function_tool(_validate_element_exists_core)
