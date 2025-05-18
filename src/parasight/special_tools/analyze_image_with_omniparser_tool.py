from typing import (
    Any,
    Dict,
    Optional,  # Added Optional
)
import base64
import os

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

        print(f"OmniParser result: {result}")

        if result.get("success") and isinstance(result.get("data"), dict) and "image" in result["data"]:
            base64_image_string = result["data"]["image"]
            # Remove the image from the result dictionary before returning
            del result["data"]["image"]

            try:
                image_bytes = base64.b64decode(base64_image_string)
                # Construct output image path
                base_name, ext = os.path.splitext(image_path)
                # Use original extension if available, otherwise default to .png
                output_image_filename = f"{base_name}_omniparser_output{ext if ext else '.png'}"
                
                with open(output_image_filename, "wb") as img_file:
                    img_file.write(image_bytes)
                print(f"Saved OmniParser processed image to: {output_image_filename}")
            except Exception as img_save_error:
                # Log error during image saving but don't let it fail the whole operation,
                # as the textual data might still be valuable.
                print(f"Error saving processed image: {img_save_error}")
                # Optionally, add this error information to the result if needed:
                # if "errors" not in result:
                #     result["errors"] = []
                # result["errors"].append(f"Failed to save processed image: {img_save_error}")

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


# Apply the function_tool decorator to the core logic function
analyze_image_with_omniparser = function_tool(_analyze_image_with_omniparser_core)
