import os
from typing import Optional

from agents import function_tool
from playwright.async_api import async_playwright
from pydantic import BaseModel  # Import BaseModel


# --- Pydantic Model for take_screenshot output ---
class ScreenshotResultOutput(BaseModel):
    success: bool
    file_path: str  # Path to the saved screenshot file
    url: Optional[str] = None
    browser_type: Optional[str] = None
    error: Optional[str] = None


# --- End Pydantic Model ---


# Core logic function (without decorator)
async def _take_screenshot_core(
    url: str, output_file: str, wait_time: int
) -> ScreenshotResultOutput:  # Use Pydantic model for return type
    """
    Navigate to a URL and take a screenshot using Playwright, saving it to a file.

    Args:
        url: The URL to navigate to
        output_file: Path to save the screenshot
        wait_time: Time to wait after page load in milliseconds

    Returns:
        Pydantic model instance with screenshot results and metadata
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

            # Save screenshot to file
            await page.screenshot(path=output_file, full_page=True)
            # Return Pydantic model instance
            return ScreenshotResultOutput(success=True, file_path=os.path.abspath(output_file), url=url)

        except Exception as e:
            # Return Pydantic model instance on error
            return ScreenshotResultOutput(success=False, error=str(e), url=url, file_path=output_file)
        finally:
            await browser.close()


# Apply the function_tool decorator to the core logic function
take_screenshot = function_tool(_take_screenshot_core)
