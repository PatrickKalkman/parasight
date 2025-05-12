from typing import Any, Dict

from agents import function_tool

from parasight.special_tools.analyze_image_with_omniparser_tool import analyze_image_with_omniparser
from parasight.special_tools.find_elements_tool import find_elements_by_description
from parasight.special_tools.take_screenshot_tool import take_screenshot


@function_tool
async def validate_element_exists(url: str, element_description: str, wait_time: int = 1000) -> Dict[str, Any]:
    """
    Navigate to a URL and validate if an element exists on the page.

    Args:
        url: The URL to navigate to
        element_description: Description of the element to find
        wait_time: Time to wait after page load in milliseconds

    Returns:
        Validation result with element details if found
    """
    # Take a screenshot
    screenshot_result = await take_screenshot(url=url, wait_time=wait_time, output_format="base64")

    if not screenshot_result.get("success", False):
        return {"success": False, "error": screenshot_result.get("error", "Failed to take screenshot")}

    # Analyze the screenshot with OmniParser
    analysis_result = await analyze_image_with_omniparser(
        image_source=screenshot_result, source_type="screenshot_result"
    )

    if not analysis_result.get("success", False):
        return {"success": False, "error": analysis_result.get("error", "Failed to analyze image")}

    # Find matching elements
    find_result = find_elements_by_description(parsed_data=analysis_result, description=element_description)

    if not find_result.get("success", False):
        return {"success": False, "error": find_result.get("error", "Failed to find elements")}

    # Check if any matching elements were found
    matches_found = find_result.get("matches_found", 0)
    if matches_found > 0:
        return {
            "success": True,
            "element_exists": True,
            "matches_found": matches_found,
            "matching_elements": find_result.get("matching_elements", []),
        }
    else:
        return {
            "success": True,
            "element_exists": False,
            "error": f"No elements matching '{element_description}' found on the page",
        }
