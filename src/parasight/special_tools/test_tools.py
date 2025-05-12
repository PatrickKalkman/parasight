import asyncio
import json

# Import the tools defined above
from parasight.special_tools.analyze_image_with_omniparser_tool import analyze_image_with_omniparser
from parasight.special_tools.extract_text_tool import extract_text_from_elements
from parasight.special_tools.find_elements_tool import find_elements_by_description
from parasight.special_tools.take_screenshot_tool import take_screenshot
from parasight.special_tools.validate_element_exists_tool import validate_element_exists


async def test_tools():
    print("=== Testing take_screenshot ===")
    # Returns ScreenshotResultOutput model
    # Call the underlying function using .func
    screenshot_result = await take_screenshot.func(
        url="https://titan-management.streamingbuzz.com", output_format="file", output_file="example_screenshot.png"
    )
    # Use model_dump_json for Pydantic models
    print(f"Screenshot result: {screenshot_result.model_dump_json(indent=2)}")
    print()

    print("=== Testing analyze_image_with_omniparser ===")
    # Call with image_path
    # Call the underlying function using .func
    analysis_result = await analyze_image_with_omniparser.func(
        image_path="example_screenshot.png" # Use image_path argument
    )
    # analysis_result is still a Dict
    print(f"Analysis result status: {analysis_result.get('success')}")
    # Safely access nested keys
    data = analysis_result.get("data", {}) if isinstance(analysis_result, dict) else {}
    content_list = data.get("parsed_content_list", []) if isinstance(data, dict) else []
    print(f"Number of elements: {len(content_list)}")
    print()

    print("=== Testing find_elements_by_description ===")
    # find_elements expects OmniParserResultInput model, but analysis_result is Dict.
    # This might fail if the dict structure doesn't perfectly match the model.
    # Ideally, convert analysis_result dict to OmniParserResultInput model here.
    # Call the underlying function using .func
    find_result = find_elements_by_description.func(parsed_data=analysis_result, description="Example Domain")
    # Use model_dump_json for Pydantic models
    print(f"Find result: {find_result.model_dump_json(indent=2)}")
    print()

    print("=== Testing extract_text_from_elements ===")
    # extract_text_from_elements expects OmniParserResultInput model, but analysis_result is Dict.
    # This might fail if the dict structure doesn't perfectly match the model.
    # Ideally, convert analysis_result dict to OmniParserResultInput model here.
    # Call the underlying function using .func
    extract_result = extract_text_from_elements.func(parsed_data=analysis_result)
    # Use model_dump_json for Pydantic models
    print(f"Extract result: {extract_result.model_dump_json(indent=2)}")
    print()

    print("=== Testing validate_element_exists ===")
    # Call the underlying function using .func
    validate_result = await validate_element_exists.func(
        url="https://titan-management.streamingbuzz.com", element_description="Example Domain"
    )
    print(f"Validation result: {json.dumps(validate_result, indent=2)}")
    print()


if __name__ == "__main__":
    asyncio.run(test_tools())
