import base64
import os
from typing import Literal, Optional

from agents import function_tool
from playwright.async_api import async_playwright
from pydantic import BaseModel  # Import BaseModel


# --- Pydantic Model for take_screenshot output ---
class ScreenshotResultOutput(BaseModel):
    success: bool
    file_path: Optional[str] = None  # Only for file output
    image_base64: Optional[str] = None  # Only for base64 output
    url: Optional[str] = None
    browser_type: Optional[str] = None
    content_type: Optional[str] = None  # Only for base64 output
    error: Optional[str] = None


# --- End Pydantic Model ---


# Core logic function (without decorator)
async def _take_screenshot_core(
    url: str, output_format: Literal["base64", "file"], output_file: Optional[str], wait_time: int
) -> ScreenshotResultOutput:  # Use Pydantic model for return type
    """
    Navigate to a URL and take a screenshot using Playwright.

    Args:
        url: The URL to navigate to
        output_format: Whether to return the screenshot as a base64 string or save it to a file
        output_file: Path to save the screenshot (only used when output_format is "file")
        wait_time: Time to wait after page load in milliseconds

    Returns:
        Dictionary with screenshot results and metadata
    """
    async with async_playwright() as p:
        # Select browser based on type
        browser = await p.chromium.launch(headless=True)
        # Create page with specified viewport
        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        try:
            # Navigate to URL
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Wait additional time if specified
            if wait_time > 0:
                await page.wait_for_timeout(wait_time)

            if output_format == "file":
                # Save screenshot to file
                if not output_file:
                    output_file = f"screenshot_{url.replace('://', '_').replace('/', '_')}.png"

                await page.screenshot(path=output_file, full_page=True)
                # Return Pydantic model instance
                return ScreenshotResultOutput(success=True, file_path=os.path.abspath(output_file), url=url)
            else:
                # Return base64 encoded image
                screenshot_bytes = await page.screenshot(full_page=True)
                # Return Pydantic model instance
                return ScreenshotResultOutput(
                    success=True,
                    image_base64=base64.b64encode(screenshot_bytes).decode("utf-8"),
                    url=url,
                    content_type="image/png",
                )

        except Exception as e:
            # Return Pydantic model instance on error
            return ScreenshotResultOutput(success=False, error=str(e), url=url)
        finally:
            await browser.close()


# Apply the function_tool decorator to the core logic function
take_screenshot = function_tool(_take_screenshot_core)
