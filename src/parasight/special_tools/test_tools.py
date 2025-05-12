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
    screenshot_result = await take_screenshot(
        url="https://titan-management.streamingbuzz.com", output_format="file", output_file="example_screenshot.png"
    )
    print(f"Screenshot result: {json.dumps(screenshot_result, indent=2)}")
    print()

    print("=== Testing analyze_image_with_omniparser ===")
    analysis_result = await analyze_image_with_omniparser(
        image_source="example_screenshot.png", source_type="file_path"
    )
    print(f"Analysis result status: {analysis_result.get('success')}")
    print(f"Number of elements: {len(analysis_result.get('data', {}).get('parsed_content_list', []))}")
    print()

    print("=== Testing find_elements_by_description ===")
    find_result = find_elements_by_description(parsed_data=analysis_result, description="Example Domain")
    print(f"Find result: {json.dumps(find_result, indent=2)}")
    print()

    print("=== Testing extract_text_from_elements ===")
    extract_result = extract_text_from_elements(parsed_data=analysis_result)
    print(f"Extract result: {json.dumps(extract_result, indent=2)}")
    print()

    print("=== Testing validate_element_exists ===")
    validate_result = await validate_element_exists(
        url="https://titan-management.streamingbuzz.com", element_description="Example Domain"
    )
    print(f"Validation result: {json.dumps(validate_result, indent=2)}")
    print()


if __name__ == "__main__":
    asyncio.run(test_tools())
