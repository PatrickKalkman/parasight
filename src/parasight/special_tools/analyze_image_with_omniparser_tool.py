from typing import (
    Any,
    Dict,
    Optional,  # Added Optional
)

from agents import function_tool

from parasight.helpers.omni_parser_client import OmniParserClient


# Core logic function (without decorator)
async def _analyze_image_with_omniparser_core(
    image_path: str,
    box_threshold: float,
    iou_threshold: float,
) -> Dict[str, Any]:  # Keep Dict return for now, ideally Pydantic
    """
    Analyze an image using the OmniParser service.

    Args:
        image_path: Path to the image file.
        box_threshold: Threshold for box detection.
        iou_threshold: IOU threshold for box detection.

    Returns:
        Analysis results from OmniParser (as a dictionary).
    """
    box_threshold = 0.05
    iou_threshold = 0.1

    image_data: Optional[bytes] = None
    try:
        # Load image data from path
        with open(image_path, "rb") as f:
            image_data = f.read()

        omniparser_client = OmniParserClient(base_url="http://192.168.1.28:7860")
        result = await omniparser_client.process_image(
            image_data=image_data, box_threshold=box_threshold, iou_threshold=iou_threshold
        )

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# Apply the function_tool decorator to the core logic function
analyze_image_with_omniparser = function_tool(_analyze_image_with_omniparser_core)
