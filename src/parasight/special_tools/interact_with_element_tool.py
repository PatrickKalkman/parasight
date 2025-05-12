import base64
from typing import Any, Dict, Literal, Optional

from agents import function_tool
from playwright.async_api import async_playwright


@function_tool
async def interact_with_element(
    element: Dict[str, Any],
    action: Literal["click", "hover", "type", "scroll_to_view"],
    browser_state: Dict[str, Any],
    text_to_type: Optional[str] = None,
    wait_after_action: int = 500,
) -> Dict[str, Any]:
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
            url = browser_state.get("url")
            if not url:
                return {"success": False, "error": "No URL provided in browser state"}

            await page.goto(url, wait_until="networkidle")

            # Get element position
            position = element.get("position", {})
            x, y = position.get("x"), position.get("y")

            if not (x is not None and y is not None):
                return {"success": False, "error": "Element position not provided"}

            # Perform the requested action
            if action == "click":
                await page.mouse.click(x, y)
                result = {"action_performed": "click", "position": {"x": x, "y": y}}

            elif action == "hover":
                await page.mouse.move(x, y)
                result = {"action_performed": "hover", "position": {"x": x, "y": y}}

            elif action == "type":
                if not text_to_type:
                    return {"success": False, "error": "No text provided for type action"}

                await page.mouse.click(x, y)
                await page.keyboard.type(text_to_type)
                result = {"action_performed": "type", "position": {"x": x, "y": y}, "text": text_to_type}

            elif action == "scroll_to_view":
                # Use JavaScript to scroll the element into view
                await page.evaluate(f"window.scrollTo({x}, {y})")
                result = {"action_performed": "scroll_to_view", "position": {"x": x, "y": y}}

            else:
                return {"success": False, "error": f"Unsupported action: {action}"}

            # Wait after action if specified
            if wait_after_action > 0:
                await page.wait_for_timeout(wait_after_action)

            # Take a screenshot after the action
            screenshot_bytes = await page.screenshot()
            result["screenshot_after_action"] = base64.b64encode(screenshot_bytes).decode("utf-8")

            # Get the current URL (might have changed after action)
            result["current_url"] = page.url

            return {"success": True, "result": result}

        except Exception as e:
            return {"success": False, "error": str(e)}

        finally:
            await browser.close()
