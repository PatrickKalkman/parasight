import base64
from typing import List, Literal, Optional

from agents import function_tool
from playwright.async_api import async_playwright
from pydantic import BaseModel


# Keep your existing models
class PositionModel(BaseModel):
    x: float
    y: float


class ElementInputModel(BaseModel):
    position: PositionModel


class BrowserStateInputModel(BaseModel):
    url: str


class InteractionSuccessResultModel(BaseModel):
    action_performed: Literal["click", "hover", "type", "scroll_to_view"]
    position: PositionModel
    text: Optional[str] = None
    screenshot_after_action: str
    current_url: str


class InteractionOutputModel(BaseModel):
    success: bool
    result: Optional[InteractionSuccessResultModel]
    error: Optional[str]


# New model for sequence of interactions
class InteractionSequenceModel(BaseModel):
    element: ElementInputModel
    action: Literal["click", "hover", "type", "scroll_to_view"]
    text_to_type: Optional[str]
    wait_after_action: int


# Updated core function to handle multiple interactions
async def _interact_with_element_sequence_core(
    interactions: List[InteractionSequenceModel],
    browser_state: BrowserStateInputModel,
    take_screenshots: bool,
) -> List[InteractionOutputModel]:
    """
    Perform a sequence of interactions with elements on the page using a single Playwright session.

    Args:
        interactions: List of interactions to perform
        browser_state: Information about the browser state (URL, etc.)
        take_screenshots: Whether to take screenshots after each action

    Returns:
        List of results for each interaction
    """
    results = []

    take_screenshots = True
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to False for debugging
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        try:
            # Navigate to the initial URL from browser state
            if not browser_state.url:
                results.append(
                    InteractionOutputModel(success=False, error="No URL provided in browser state", result=None)
                )
                return results

            await page.goto(browser_state.url, wait_until="networkidle")

            viewport_size = page.viewport_size
            if not viewport_size:
                results.append(
                    InteractionOutputModel(success=False, error="Could not determine page viewport size.", result=None)
                )
                await browser.close() # Ensure browser is closed before returning
                return results

            # Perform each interaction in sequence
            for i, interaction in enumerate(interactions):
                element = interaction.element
                action = interaction.action
                text_to_type = interaction.text_to_type
                wait_after_action = interaction.wait_after_action

                # Get element position (these are normalized)
                normalized_x, normalized_y = element.position.x, element.position.y

                # Scale to pixel coordinates
                pixel_x = int(normalized_x * viewport_size['width'])
                pixel_y = int(normalized_y * viewport_size['height'])

                # Perform the requested action
                result_data: dict = {}
                try:
                    if action == "click":
                        await page.mouse.click(pixel_x, pixel_y)
                        result_data = {"action_performed": "click", "position": {"x": pixel_x, "y": pixel_y}}

                    elif action == "hover":
                        await page.mouse.move(pixel_x, pixel_y)
                        result_data = {"action_performed": "hover", "position": {"x": pixel_x, "y": pixel_y}}

                    elif action == "type":
                        if not text_to_type:
                            results.append(
                                InteractionOutputModel(
                                    success=False,
                                    error=f"No text provided for type action at step {i + 1}",
                                    result=None,
                                )
                            )
                            continue

                        print(f"Step {i + 1}: Typing text: {text_to_type} at position ({pixel_x}, {pixel_y})")
                        await page.mouse.click(pixel_x, pixel_y) # Click at the target before typing
                        await page.keyboard.type(text_to_type)
                        result_data = {"action_performed": "type", "position": {"x": pixel_x, "y": pixel_y}, "text": text_to_type}

                    elif action == "scroll_to_view":
                        await page.evaluate(f"window.scrollTo({pixel_x}, {pixel_y})")
                        result_data = {"action_performed": "scroll_to_view", "position": {"x": pixel_x, "y": pixel_y}}

                    else:
                        results.append(
                            InteractionOutputModel(
                                success=False, error=f"Unsupported action: {action} at step {i + 1}", result=None
                            )
                        )
                        continue

                    # Wait after action if specified
                    if wait_after_action > 0:
                        await page.wait_for_timeout(wait_after_action)

                    # Take and save screenshot if requested
                    if take_screenshots:
                        screenshot_bytes = await page.screenshot()
                        result_data["screenshot_after_action"] = base64.b64encode(screenshot_bytes).decode("utf-8")

                        # Save the screenshot to a file
                        screenshot_path = f"screenshot_after_step_{i + 1}_{action}.png"
                        with open(screenshot_path, "wb") as f:
                            f.write(screenshot_bytes)
                    else:
                        # Provide a placeholder if screenshots disabled
                        result_data["screenshot_after_action"] = ""

                    # Get the current URL (might have changed after action)
                    result_data["current_url"] = page.url

                    # Ensure position in result_data is a PositionModel instance or dict
                    # The "position" key in result_data should already hold a dict like {"x": pixel_x, "y": pixel_y}
                    # from the action-specific assignments. This explicit assignment ensures it's a PositionModel.
                    result_data["position"] = PositionModel(x=pixel_x, y=pixel_y) # Use pixel_x, pixel_y

                    success_payload = InteractionSuccessResultModel(**result_data)
                    results.append(InteractionOutputModel(success=True, result=success_payload, error=None))

                except Exception as e:
                    results.append(
                        InteractionOutputModel(success=False, error=f"Error in step {i + 1}: {str(e)}", result=None)
                    )

            return results

        except Exception as e:
            # Global exception handler
            if not results:  # If error happened before any actions were performed
                results.append(InteractionOutputModel(success=False, error=str(e), result=None))
            return results

        finally:
            await browser.close()


interact_with_element_sequence = function_tool(_interact_with_element_sequence_core)
