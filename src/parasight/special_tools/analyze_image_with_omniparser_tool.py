import base64
import os
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
        print(f"Starting analysis of image: {image_path}")
        # Load image data from path
        with open(image_path, "rb") as f:
            image_data = f.read()
        print(f"Successfully loaded image data, size: {len(image_data)} bytes")

        print("Connecting to OmniParser at http://192.168.1.28:7860")
        omniparser_client = OmniParserClient(base_url="http://192.168.1.28:7860")
        print(f"Sending image to OmniParser with box_threshold={box_threshold}, iou_threshold={iou_threshold}")
        result = await omniparser_client.process_image(
            image_data=image_data, box_threshold=box_threshold, iou_threshold=iou_threshold
        )
        print(f"Received response from OmniParser: {result}")

        # Check if the response is successful (no 'success' key means success, 'success': False means error)
        is_successful = "success" not in result or result.get("success", True)
        print(f"Response is successful: {is_successful}")

        # Check if image is directly in the result or in a nested data dictionary
        if is_successful and "image" in result:
            print("Found image data directly in the response")
            base64_image_string = result["image"]
        elif is_successful and isinstance(result.get("data"), dict) and "image" in result["data"]:
            print("Found image data in the nested data dictionary")
            base64_image_string = result["data"]["image"]
        else:
            base64_image_string = None
            
        if base64_image_string:

            try:
                print(f"Decoding base64 image data (length: {len(base64_image_string)})")
                image_bytes = base64.b64decode(base64_image_string)
                print(f"Successfully decoded image data, size: {len(image_bytes)} bytes")

                # Construct output image path
                base_name, ext = os.path.splitext(image_path)
                # Use original extension if available, otherwise default to .png
                output_image_filename = f"{base_name}_omniparser_output{ext if ext else '.png'}"
                print(f"Will save processed image to: {output_image_filename}")

                with open(output_image_filename, "wb") as img_file:
                    img_file.write(image_bytes)
                print(f"Saved OmniParser processed image to: {output_image_filename}")
            except Exception as img_save_error:
                # Log error during image saving but don't let it fail the whole operation,
                # as the textual data might still be valuable.
                print(f"Error saving processed image: {img_save_error}")
                import traceback

                print(f"Detailed error: {traceback.format_exc()}")
        else:
            print(f"No image data found in response or response unsuccessful. Response keys: {result.keys()}")
            if "data" in result:
                print(
                    f"Data keys: {result['data'].keys() if isinstance(result['data'], dict) else 'data is not a dict'}"
                )

        # Remove image data from result before returning
        if "image" in result:
            del result["image"]
        elif "data" in result and isinstance(result["data"], dict) and "image" in result["data"]:
            del result["data"]["image"]

        return result
    except Exception as e:
        print(f"Exception in analyze_image_with_omniparser: {e}")
        import traceback

        print(f"Detailed error: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}


# Apply the function_tool decorator to the core logic function
analyze_image_with_omniparser = function_tool(_analyze_image_with_omniparser_core)
