from typing import List, Optional  # Add List

from agents import function_tool
from pydantic import BaseModel, Field  # Import Pydantic components


# --- Pydantic Models ---
class Position(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None


class OmniParserElement(BaseModel):
    text: Optional[str] = ""
    center_x: Optional[float] = Field(None)
    center_y: Optional[float] = Field(None)
    element_type: Optional[str] = "unknown"
    # model_config = ConfigDict(extra='allow') # Removed to enforce strict schema


class OmniParserData(BaseModel):
    parsed_content_list: List[OmniParserElement] = []
    # model_config = ConfigDict(extra='allow') # Removed to enforce strict schema


class OmniParserResultInput(BaseModel):  # Input model
    success: bool
    data: Optional[OmniParserData] = None
    error: Optional[str] = None
    # model_config = ConfigDict(extra='allow') # Removed to enforce strict schema


class ExtractedElementOutput(BaseModel):  # Output model for one element
    text: str
    position: Position
    element_type: str


class ExtractedTextResultOutput(BaseModel):  # Final output model
    success: bool
    element_count: Optional[int] = None
    extracted_text: Optional[List[ExtractedElementOutput]] = None
    error: Optional[str] = None


# --- End Pydantic Models ---


# Core logic function (without decorator)
def _extract_text_from_elements_core(
    parsed_data: OmniParserResultInput, element_type: Optional[str] = None
) -> ExtractedTextResultOutput:
    """
    Extract text from elements in OmniParser results, optionally filtered by type.

    Args:
        parsed_data: The parsed data from OmniParser
        element_type: Optional filter for element type

    Returns:
        Pydantic model instance with extracted text from elements
    """
    # Pydantic automatically validates/converts the input dict to OmniParserResultInput
    if not parsed_data.success:
        # Return model instance even on failure
        return ExtractedTextResultOutput(success=False, error=parsed_data.error or "Invalid parsed data")

    if not parsed_data.data or not parsed_data.data.parsed_content_list:
        return ExtractedTextResultOutput(success=False, error="No elements found in parsed data")

    extracted_elements_output: List[ExtractedElementOutput] = []

    for element in parsed_data.data.parsed_content_list:
        # Skip elements that don't match the requested type
        if element_type and element.element_type != element_type:
            continue

        text = (element.text or "").strip()
        if text:
            # Ensure element_type is not None before passing to model
            element_type_str = element.element_type or "unknown"
            extracted_elements_output.append(
                ExtractedElementOutput(
                    text=text,
                    position=Position(x=element.center_x, y=element.center_y),
                    element_type=element_type_str,
                )
            )

    return ExtractedTextResultOutput(
        success=True, element_count=len(extracted_elements_output), extracted_text=extracted_elements_output
    )


# Apply the function_tool decorator to the core logic function
extract_text_from_elements = function_tool(_extract_text_from_elements_core)
