import asyncio
import base64

# Import the core functions and necessary models
from parasight.special_tools.analyze_image_with_omniparser_tool import _analyze_image_with_omniparser_core
from parasight.special_tools.extract_text_tool import (
    OmniParserResultInput,  # Import the input model
    _extract_text_from_elements_core,
)
from parasight.special_tools.interact_with_element_tool import (
    BrowserStateInputModel,
    ElementInputModel,
    InteractionSequenceModel,
    PositionModel,
    _interact_with_element_sequence_core,
)
from parasight.special_tools.take_screenshot_tool import _take_screenshot_core
from parasight.special_tools.validate_element_exists_tool import _validate_element_exists_core


async def get_page_dimensions(url):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        dimensions = await page.evaluate("""() => {
            return {
                width: window.innerWidth,
                height: window.innerHeight
            }
        }""")
        await browser.close()
        return dimensions


async def find_element_position(url, element_description, screen_width, screen_height):
    """Find an element by description and convert its normalized coordinates to pixel coordinates."""
    validate_result = await _validate_element_exists_core(url=url, element_description=element_description)

    if validate_result["success"] and validate_result["element_exists"] and validate_result["matching_elements"]:
        first_match = validate_result["matching_elements"][0]
        normalized_x = first_match["position"]["x"]
        normalized_y = first_match["position"]["y"]

        # Convert normalized coordinates to actual pixel coordinates
        pixel_x = int(normalized_x * screen_width)
        pixel_y = int(normalized_y * screen_height)

        print(f"Element '{element_description}' found:")
        print(f"  Normalized coordinates: ({normalized_x}, {normalized_y})")
        print(f"  Pixel coordinates: ({pixel_x}, {pixel_y})")

        return PositionModel(x=pixel_x, y=pixel_y)
    else:
        print(f"Element '{element_description}' not found")
        return None


async def test_tools():
    url = "http://192.168.1.28:3000/"
    screenshot_output_file = "example_screenshot.png"

    print("=== Testing _take_screenshot_core ===")
    screenshot_result = await _take_screenshot_core(url=url, output_file=screenshot_output_file, wait_time=500)
    print(f"Screenshot result: {screenshot_result.model_dump_json(indent=2)}")
    print()

    print("=== Testing _analyze_image_with_omniparser_core ===")
    analysis_result: dict = await _analyze_image_with_omniparser_core(
        image_path=screenshot_output_file, image_base64=None, box_threshold=0.05, iou_threshold=0.1
    )
    print(f"Analysis result status: {analysis_result.get('success')}")

    data = analysis_result.get("data", {}) if isinstance(analysis_result, dict) else {}
    content_list = data.get("parsed_content_list", []) if isinstance(data, dict) else []
    annotated_image = data.get("image", "") if isinstance(data, dict) else ""
    print(f"Number of elements: {len(content_list)}")

    if annotated_image:
        with open("annotated_image.png", "wb") as f:
            f.write(base64.b64decode(annotated_image))

    try:
        parsed_data_input = OmniParserResultInput(**analysis_result)
    except Exception as e:
        print(f"Error converting analysis_result to OmniParserResultInput: {e}")
        return

    print("=== Testing _extract_text_from_elements_core ===")
    extract_result = _extract_text_from_elements_core(parsed_data=parsed_data_input)
    print(f"Extract result: {extract_result.model_dump_json(indent=2)}")
    print()
    await test_login_flow(url="http://192.168.1.28:3000/", username="demo", password="password123")


# Example usage function
async def test_login_flow(url, username, password):
    # Get browser dimensions first

    browser_dimensions = await get_page_dimensions(url)
    screen_width = browser_dimensions["width"]
    screen_height = browser_dimensions["height"]

    # Find positions for all required elements
    username_position = await find_element_position(url, "Enter your username", screen_width, screen_height)
    password_position = await find_element_position(url, "Enter your password", screen_width, screen_height)
    login_button_position = await find_element_position(url, "Login", screen_width, screen_height)

    # Create element models
    username_element = ElementInputModel(position=username_position)
    password_element = ElementInputModel(position=password_position)
    login_button_element = ElementInputModel(position=login_button_position)

    # Create browser state
    browser_state = BrowserStateInputModel(url=url)

    # Create sequence of interactions
    interactions = [
        InteractionSequenceModel(element=username_element, action="click", wait_after_action=200),
        InteractionSequenceModel(element=username_element, action="type", text_to_type=username, wait_after_action=500),
        InteractionSequenceModel(element=password_element, action="click", wait_after_action=200),
        InteractionSequenceModel(element=password_element, action="type", text_to_type=password, wait_after_action=500),
        InteractionSequenceModel(element=login_button_element, action="click", wait_after_action=2000),
    ]

    # Execute the sequence
    results = await _interact_with_element_sequence_core(interactions=interactions, browser_state=browser_state)

    # Process results
    for i, result in enumerate(results):
        print(f"\nResult for action {i + 1}:")
        print(f"Success: {result.success}")
        if result.success:
            print(f"Action performed: {result.result.action_performed}")
            if result.result.action_performed == "type":
                print(f"Text typed: {result.result.text}")
        else:
            print(f"Error: {result.error}")

    # Return True if login was successful (you'll need to determine this based on the results)
    return all(result.success for result in results)


if __name__ == "__main__":
    asyncio.run(test_tools())
