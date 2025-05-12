import base64
from typing import Any, Dict, Literal

from agents import function_tool

from parasight.helpers.omni_parser_client import OmniParserClient


@function_tool
async def analyze_image_with_omniparser(
    image_path: str = None,
    image_base64: str = None,
    source_type: Literal["file_path", "base64"] = "file_path",
    box_threshold: float = 0.05,
    iou_threshold: float = 0.1,
) -> Dict[str, Any]:
    """
    Analyze an image using the OmniParser service.


    Args:
        image_source: Source of the image (file path, base64 string, or screenshot result)
        source_type: Type of the image source ("file_path", "base64", or "screenshot_result")
        box_threshold: Threshold for box detection
        iou_threshold: IOU threshold for box detection

    Returns:
        Analysis results from OmniParser
    """
    try:
        # Get image data based on source type
        if source_type == "file_path":
            with open(image_source, "rb") as f:
                image_data = f.read()
        elif source_type == "base64":
            image_data = base64.b64decode(image_source)
        elif source_type == "screenshot_result":
            # Assuming image_source is a dictionary with image_base64 field
            if isinstance(image_source, dict) and "image_base64" in image_source:
                image_data = base64.b64decode(image_source["image_base64"])
            else:
                return {"success": False, "error": "Invalid screenshot result format"}
        else:
            return {"success": False, "error": f"Unsupported source type: {source_type}"}

        omniparser_client = OmniParserClient(base_url="http://192.168.1.28:7860")
        result = await omniparser_client.process_image(
            image_data=image_data, box_threshold=box_threshold, iou_threshold=iou_threshold
        )

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}
