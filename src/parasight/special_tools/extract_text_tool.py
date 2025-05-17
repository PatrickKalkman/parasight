import ast
import re
from typing import Dict, List, Optional, Tuple  # Add List

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
    image: str
    parsed_content_list: str


class OmniParserResultInput(BaseModel):  # Input model
    success: bool
    data: Optional[OmniParserData] = None
    error: Optional[str] = None


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


# Helper function to parse coordinates string
def _parse_coordinates(coords_str: str) -> Dict[str, List[float]]:
    """Parses the label_coordinates string into a dictionary."""
    try:
        # Replace np.float32() wrapper to make it valid literal syntax
        clean_coords_str = re.sub(r"np\.float32\(([^)]+)\)", r"\1", coords_str)
        # Safely evaluate the string as a Python literal
        coords_dict = ast.literal_eval(clean_coords_str)
        if isinstance(coords_dict, dict):
            # Basic validation: ensure values are lists of numbers (or at least lists)
            return {
                k: v
                for k, v in coords_dict.items()
                if isinstance(v, list)  # and all(isinstance(n, (int, float)) for n in v) # Stricter check if needed
            }
        return {}
    except (ValueError, SyntaxError, TypeError):
        # Handle potential errors during parsing
        return {}


# Helper function to parse a single line from parsed_content_list
def _parse_element_line(line: str) -> Optional[Tuple[str, str, str]]:
    """Parses a line like 'Text Box ID 0: UI' into (type, id, text)."""
    match = re.match(r"^(.*?)\s+ID\s+(\d+):\s+(.*)$", line.strip())
    if match:
        element_type_parsed = match.group(1).strip()
        element_id_parsed = match.group(2).strip()
        text_parsed = match.group(3).strip()
        return element_type_parsed, element_id_parsed, text_parsed
    return None


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
