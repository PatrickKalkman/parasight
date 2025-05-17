from typing import Any, Dict

from agents import function_tool

from parasight.special_tools.analyze_image_with_omniparser_tool import _analyze_image_with_omniparser_core

# Import Pydantic models used by the tools
from parasight.special_tools.extract_text_tool import OmniParserResultInput  # Import the input model
from parasight.special_tools.find_elements_tool import FindElementsResultOutput, _find_elements_by_description_core
from parasight.special_tools.take_screenshot_tool import ScreenshotResultOutput, _take_screenshot_core


# Core logic function (without decorator)
async def _validate_element_exists_core(url: str, element_description: str, wait_time: int) -> Dict[str, Any]:
    """
    Navigate to a URL and validate if an element exists on the page.

    Args:
        url: The URL to navigate to
        element_description: Description of the element to find
        wait_time: Time to wait after page load in milliseconds

    Returns:
        Validation result with element details if found
    """

    wait_time = 1000

    # Take a screenshot (returns ScreenshotResultOutput model)
    screenshot_result: ScreenshotResultOutput = await _take_screenshot_core(
        url=url, wait_time=wait_time, output_format="base64"
    )

    if not screenshot_result.success:
        return {"success": False, "error": screenshot_result.error or "Failed to take screenshot"}

    if not screenshot_result.image_base64:
        return {"success": False, "error": "Screenshot taken but no base64 image data found"}

    # Analyze the screenshot with OmniParser (returns Dict for now, ideally should be Pydantic too)
    # Pass base64 data directly
    analysis_result = await _analyze_image_with_omniparser_core(
        image_base64=screenshot_result.image_base64  # Removed source_type argument
    )

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
        parsed_data=parsed_data_input, description=element_description
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


# Apply the function_tool decorator to the core logic function
validate_element_exists = function_tool(_validate_element_exists_core)
