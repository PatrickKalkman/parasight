import asyncio
import json

# Import the core functions and necessary models
from parasight.special_tools.analyze_image_with_omniparser_tool import _analyze_image_with_omniparser_core
from parasight.special_tools.extract_text_tool import (
    OmniParserResultInput,  # Import the input model
    _extract_text_from_elements_core,
)
from parasight.special_tools.find_elements_tool import _find_elements_by_description_core
from parasight.special_tools.take_screenshot_tool import _take_screenshot_core
from parasight.special_tools.validate_element_exists_tool import _validate_element_exists_core


async def test_tools():
    print("=== Testing _take_screenshot_core ===")
    # Returns ScreenshotResultOutput model
    # Call the core function directly
    screenshot_result = await _take_screenshot_core(
        url="https://titan-management.streamingbuzz.com", output_format="file", output_file="example_screenshot.png"
    )
    # Use model_dump_json for Pydantic models
    print(f"Screenshot result: {screenshot_result.model_dump_json(indent=2)}")
    print()

    print("=== Testing _analyze_image_with_omniparser_core ===")
    # Call with image_path
    # Call the core function directly
    analysis_result: dict = await _analyze_image_with_omniparser_core(
        image_path="example_screenshot.png"  # Use image_path argument
    )
    # analysis_result is a Dict
    print(f"Analysis result status: {analysis_result.get('success')}")
    # Safely access nested keys
    data = analysis_result.get("data", {}) if isinstance(analysis_result, dict) else {}
    content_list = data.get("parsed_content_list", []) if isinstance(data, dict) else []
    print(f"Number of elements: {len(content_list)}")

    # Convert the analysis_result dict to the Pydantic model expected by downstream tools
    # This assumes the dict structure from analyze_image matches OmniParserResultInput
    try:
        parsed_data_input = OmniParserResultInput(**analysis_result)
    except Exception as e:
        print(f"Error converting analysis_result to OmniParserResultInput: {e}")
        # Handle error appropriately, maybe skip subsequent tests
        return

    print()

    print("=== Testing _find_elements_by_description_core ===")
    # Call the core function directly, passing the Pydantic model instance
    find_result = _find_elements_by_description_core(parsed_data=parsed_data_input, description="Example Domain")
    # Use model_dump_json for Pydantic models
    print(f"Find result: {find_result.model_dump_json(indent=2)}")
    print()

    print("=== Testing _extract_text_from_elements_core ===")
    # Call the core function directly, passing the Pydantic model instance
    extract_result = _extract_text_from_elements_core(parsed_data=parsed_data_input)
    # Use model_dump_json for Pydantic models
    print(f"Extract result: {extract_result.model_dump_json(indent=2)}")
    print()

    print("=== Testing _validate_element_exists_core ===")
    # Call the core function directly
    validate_result = await _validate_element_exists_core(
        url="https://titan-management.streamingbuzz.com", element_description="Example Domain"
    )
    # validate_result is a Dict
    print(f"Validation result: {json.dumps(validate_result, indent=2)}")
    print()


if __name__ == "__main__":
    asyncio.run(test_tools())
