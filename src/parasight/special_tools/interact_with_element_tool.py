import base64
from typing import Literal, Optional

from agents import function_tool
from playwright.async_api import async_playwright
from pydantic import BaseModel


# Pydantic Models for input and output structures
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
    result: Optional[InteractionSuccessResultModel] = None
    error: Optional[str] = None


# Core logic function (without decorator)
async def _interact_with_element_core(
    element: ElementInputModel,
    action: Literal["click", "hover", "type", "scroll_to_view"],
    browser_state: BrowserStateInputModel,
    text_to_type: Optional[str] = None,
    wait_after_action: int = 500,
) -> InteractionOutputModel:
    """
    Interact with an element on the page using Playwright.

    Args:
        element: Element information with position
        action: Type of interaction
        browser_state: Information about the current browser state (URL, etc.)
        text_to_type: Text to type (only used when action is "type")
        wait_after_action: Time to wait after action in milliseconds

    Returns:
        Result of the interaction
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # Navigate to the URL from browser state
            if not browser_state.url: # Should not happen if model validation is on
                return InteractionOutputModel(success=False, error="No URL provided in browser state")

            await page.goto(browser_state.url, wait_until="networkidle")

            # Get element position
            x, y = element.position.x, element.position.y

            # Perform the requested action
            result_data: dict = {}
            if action == "click":
                await page.mouse.click(x, y)
                result_data = {"action_performed": "click", "position": {"x": x, "y": y}}

            elif action == "hover":
                await page.mouse.move(x, y)
                result_data = {"action_performed": "hover", "position": {"x": x, "y": y}}

            elif action == "type":
                if not text_to_type:
                    return InteractionOutputModel(success=False, error="No text provided for type action")

                await page.mouse.click(x, y)
                await page.keyboard.type(text_to_type)
                result_data = {"action_performed": "type", "position": {"x": x, "y": y}, "text": text_to_type}

            elif action == "scroll_to_view":
                # Use JavaScript to scroll the element into view
                # Note: Playwright's element.scroll_into_view_if_needed() is usually preferred
                # if we have an ElementHandle. Here, we only have coordinates.
                await page.evaluate(f"window.scrollTo({x}, {y})")
                result_data = {"action_performed": "scroll_to_view", "position": {"x": x, "y": y}}
            else:
                # This case should ideally be caught by Literal type validation earlier
                return InteractionOutputModel(success=False, error=f"Unsupported action: {action}")

            # Wait after action if specified
            if wait_after_action > 0:
                await page.wait_for_timeout(wait_after_action)

            # Take a screenshot after the action
            screenshot_bytes = await page.screenshot()
            result_data["screenshot_after_action"] = base64.b64encode(screenshot_bytes).decode("utf-8")

            # Get the current URL (might have changed after action)
            result_data["current_url"] = page.url

            # Ensure position in result_data is a PositionModel instance or dict
            result_data["position"] = PositionModel(x=x, y=y)

            success_payload = InteractionSuccessResultModel(**result_data)
            return InteractionOutputModel(success=True, result=success_payload)

        except Exception as e:
            return InteractionOutputModel(success=False, error=str(e))

        finally:
            await browser.close()


# Apply the function_tool decorator to the core logic function
interact_with_element = function_tool(_interact_with_element_core)
