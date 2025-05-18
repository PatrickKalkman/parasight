from typing import Any, Dict

from agents import function_tool

# Import Pydantic models used by the tools
from parasight.special_tools.extract_text_tool import OmniParserResultInput  # Import the input model


# Core logic function (without decorator)
def _validate_element_exists_core(analysis_result: OmniParserResultInput, element_description: str) -> Dict[str, Any]:
    """
    Validate if an element description exists within OmniParser analysis results.

    Args:
        analysis_result: The output OmniParserResultInput from the analyze_image_with_omniparser_tool.
                         This contains the parsed text content from the image.
        element_description: Description/text to find within the analysis result's parsed content.

    Returns:
        A dictionary indicating success, whether the element_description was found, and an optional error/message.
    """
    try:
        # 1. Check if analysis_result itself is valid and indicates success from OmniParser
        if not isinstance(analysis_result, OmniParserResultInput):
            return {"success": False, "element_exists": False, "error": "Invalid analysis_result type provided."}

        if not analysis_result.success:
            error_msg = analysis_result.error or "OmniParser analysis failed without a specific error message."
            return {"success": False, "element_exists": False, "error": f"Upstream OmniParser analysis failed: {error_msg}"}

        # 2. Check if the necessary data for searching is present
        if not analysis_result.data:
            return {
                "success": False,
                "element_exists": False,
                "error": "OmniParser analysis succeeded but returned no 'data' object. Cannot perform validation.",
            }
        
        # analysis_result.data is an OmniParserData instance.
        # analysis_result.data.parsed_content_list is a string (cannot be None by Pydantic model).
        # It can be an empty string, which is handled correctly by the 'in' operator.
        parsed_text_content = analysis_result.data.parsed_content_list

        # 3. Ensure element_description is a string
        if not isinstance(element_description, str):
             return {"success": False, "element_exists": False, "error": "Invalid element_description, must be a string."}

        # 4. Perform the case-insensitive search
        if element_description.lower() in parsed_text_content.lower():
            return {
                "success": True,
                "element_exists": True,
                "message": f"Element description '{element_description}' found in parsed content.",
            }
        else:
            return {
                "success": True,
                "element_exists": False,
                "message": f"Element description '{element_description}' not found in parsed content.",
            }
    except AttributeError as ae:
        # This might catch issues if analysis_result is not the expected Pydantic model.
        return {"success": False, "element_exists": False, "error": f"Malformed analysis_result structure: {str(ae)}"}
    except Exception as e:
        # Catch any other unexpected errors during the process
        return {"success": False, "element_exists": False, "error": f"An unexpected error occurred: {str(e)}"}


# Apply the function_tool decorator to the core logic function
validate_element_exists = function_tool(_validate_element_exists_core)
