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
        page = await browser.new_page()

        try:
            # Navigate to the initial URL from browser state
            if not browser_state.url:
                results.append(InteractionOutputModel(success=False, error="No URL provided in browser state"))
                return results

            await page.goto(browser_state.url, wait_until="networkidle")

            # Perform each interaction in sequence
            for i, interaction in enumerate(interactions):
                element = interaction.element
                action = interaction.action
                text_to_type = interaction.text_to_type
                wait_after_action = interaction.wait_after_action

                # Get element position
                x, y = element.position.x, element.position.y

                # Perform the requested action
                result_data: dict = {}
                try:
                    if action == "click":
                        await page.mouse.click(x, y)
                        result_data = {"action_performed": "click", "position": {"x": x, "y": y}}

                    elif action == "hover":
                        await page.mouse.move(x, y)
                        result_data = {"action_performed": "hover", "position": {"x": x, "y": y}}

                    elif action == "type":
                        if not text_to_type:
                            results.append(
                                InteractionOutputModel(
                                    success=False, error=f"No text provided for type action at step {i + 1}"
                                )
                            )
                            continue

                        print(f"Step {i + 1}: Typing text: {text_to_type} at position ({x}, {y})")
                        await page.mouse.click(x, y)
                        await page.keyboard.type(text_to_type)
                        result_data = {"action_performed": "type", "position": {"x": x, "y": y}, "text": text_to_type}

                    elif action == "scroll_to_view":
                        await page.evaluate(f"window.scrollTo({x}, {y})")
                        result_data = {"action_performed": "scroll_to_view", "position": {"x": x, "y": y}}

                    else:
                        results.append(
                            InteractionOutputModel(success=False, error=f"Unsupported action: {action} at step {i + 1}")
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
                    result_data["position"] = PositionModel(x=x, y=y)

                    success_payload = InteractionSuccessResultModel(**result_data)
                    results.append(InteractionOutputModel(success=True, result=success_payload))

                except Exception as e:
                    results.append(InteractionOutputModel(success=False, error=f"Error in step {i + 1}: {str(e)}"))

            return results

        except Exception as e:
            # Global exception handler
            if not results:  # If error happened before any actions were performed
                results.append(InteractionOutputModel(success=False, error=str(e)))
            return results

        finally:
            await browser.close()


# Keep the original single-interaction function, modified to use the sequence function
async def _interact_with_element_core(
    element: ElementInputModel,
    action: Literal["click", "hover", "type", "scroll_to_view"],
    browser_state: BrowserStateInputModel,
    text_to_type: Optional[str] = None,
    wait_after_action: int = 500,
) -> InteractionOutputModel:
    """
    Interact with a single element on the page using Playwright.

    This function is a wrapper around _interact_with_element_sequence_core that
    handles a single interaction for backward compatibility.
    """
    interaction = InteractionSequenceModel(
        element=element, action=action, text_to_type=text_to_type, wait_after_action=wait_after_action
    )

    results = await _interact_with_element_sequence_core(interactions=[interaction], browser_state=browser_state)

    # Return the first result (there should only be one)
    if results:
        return results[0]
    else:
        return InteractionOutputModel(success=False, error="No result returned from interaction")


interact_with_element = function_tool(_interact_with_element_core)
interact_with_element_sequence = function_tool(_interact_with_element_sequence_core)
