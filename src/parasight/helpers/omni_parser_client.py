import ast
import json
import logging
import os
import re # Added re
from typing import Any, Dict

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class OmniParserClient:
    """
    Client for interacting with the OmniParser REST API.
    """

    def __init__(self, base_url: str, timeout: int = 120):
        """
        Initialize the OmniParser client.

        Args:
            base_url: Base URL for the OmniParser API (e.g., "http://localhost:8000")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=timeout)

    async def process_image(
        self, image_data: bytes = None, image_path: str = None, box_threshold: float = 0.05, iou_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        Process an image using OmniParser.

        Args:
            image_data: Raw image bytes
            image_path: Path to image file
            box_threshold: Threshold for box detection (default: 0.05)
            iou_threshold: IOU threshold for box detection (default: 0.1)

        Returns:
            Processed image results with parsed content and label coordinates
        """
        if sum(x is not None for x in [image_data, image_path]) != 1:
            raise ValueError("Exactly one of image_data or image_path must be provided")

        # Prepare the image data
        if image_path:
            if not os.path.exists(image_path):
                return {"success": False, "error": f"Image file not found: {image_path}"}
            with open(image_path, "rb") as f:
                image_data = f.read()

        # Prepare form data with the image file
        files = {"image_file": image_data}

        # Prepare query parameters
        params = {"box_threshold": box_threshold, "iou_threshold": iou_threshold}

        try:
            response = await self.client.post(f"{self.base_url}/process_image", params=params, files=files)

            response.raise_for_status()
            response_text = response.text

            # Clean np.float32() calls from the response text.
            # This makes the string evaluatable by ast.literal_eval.
            cleaned_response_text = re.sub(r"np\.float32\(([^)]+)\)", r"\1", response_text)

            # Safely evaluate the cleaned string as a Python literal (dictionary).
            # This result is expected to be in the format:
            # {
            #   'success': True,
            #   'data': {
            #     'parsed_content_list': "...", # This is a string
            #     'label_coordinates': "{'id': [coords], ...}" # This is also a string
            #   }
            # }
            # The label_coordinates string will be parsed later by _parse_coordinates.
            parsed_result = ast.literal_eval(cleaned_response_text)
            
            return parsed_result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OmniParser: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP error: {e.response.status_code}", "message": e.response.text}
        except (SyntaxError, ValueError) as e:
            logger.error(f"Failed to parse OmniParser response string: '{response_text}'. Error: {e}")
            return {"success": False, "error": "Failed to parse OmniParser response", "message": str(e)}
        except Exception as e:
            logger.error(f"Error processing image with OmniParser: {str(e)}")
            return {"success": False, "error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the OmniParser API is up and running.

        Returns:
            Health check result
        """
        try:
            # For FastAPI, we can check if the /docs or /openapi.json endpoint is available
            # This is more reliable than checking a specific API endpoint
            response = await self.client.get(f"{self.base_url}/openapi.json")

            if response.status_code == 200:
                return {"success": True, "status": response.status_code, "message": "API documentation is available"}
            else:
                # Try the /docs endpoint as a fallback
                response = await self.client.get(f"{self.base_url}/docs")
                if response.status_code == 200:
                    return {
                        "success": True,
                        "status": response.status_code,
                        "message": "API documentation is available",
                    }
                else:
                    return {"success": False, "error": f"API documentation not available: {response.status_code}"}
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def close(self):
        """
        Close the HTTP client.
        """
        await self.client.aclose()
