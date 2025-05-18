from typing import Any, Dict

from agents import function_tool

# Import Pydantic models used by the tools
from parasight.special_tools.extract_text_tool import OmniParserResultInput  # Import the input model
from parasight.special_tools.find_elements_tool import FindElementsResultOutput, _find_elements_by_description_core


# Core logic function (without decorator)
def _validate_element_exists_core(analysis_result: Dict[str, Any], element_description: str) -> Dict[str, Any]:
    """
    Validate if an element exists based on OmniParser analysis results.

    Args:
        analysis_result: The output dictionary from the analyze_image_with_omniparser_tool.
        element_description: Description of the element to find within the analysis result.

    Returns:
        Validation result with element details if found.
    """

    # All subsequent operations are wrapped in a try.
    try:
        if not analysis_result or not isinstance(analysis_result, dict):
            return {"success": False, "error": "Invalid analysis_result provided. Expected a dictionary."}

        if not analysis_result.get("success", False):
            return {"success": False, "error": analysis_result.get("error", "Analysis result indicates failure.")}

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
