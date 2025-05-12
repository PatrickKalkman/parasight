import json
import logging
import os
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
            result = response.json()

            # Parse string fields if they contain JSON
            try:
                if isinstance(result.get("parsed_content_list"), str):
                    result["parsed_content_list"] = json.loads(result["parsed_content_list"])
                if isinstance(result.get("label_coordinates"), str):
                    result["label_coordinates"] = json.loads(result["label_coordinates"])
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON from response strings")

            return {"success": True, "data": result}

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from OmniParser: {e.response.status_code} - {e.response.text}")
            return {"success": False, "error": f"HTTP error: {e.response.status_code}", "message": e.response.text}
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
