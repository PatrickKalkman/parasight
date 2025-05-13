import ast
import re
from typing import Dict, List, Optional, Tuple  # Add List, Dict, Tuple

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
    label_coordinates: str  # Added field for coordinates string
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
                if isinstance(v, list) # and all(isinstance(n, (int, float)) for n in v) # Stricter check if needed
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
    parsed_data: OmniParserResultInput, element_type_filter: Optional[str] = None # Renamed for clarity
) -> ExtractedTextResultOutput:
    """
    Extract text and position from elements described in OmniParser results,
    optionally filtered by type.

    Args:
        parsed_data: The parsed data from OmniParser (as a Pydantic model).
        element_type_filter: Optional filter for element type (e.g., "Text Box").

    Returns:
        Pydantic model instance with extracted text from elements.
    """
    if not parsed_data.success:
        return ExtractedTextResultOutput(success=False, error=parsed_data.error or "OmniParser analysis failed")

    if not parsed_data.data or not parsed_data.data.parsed_content_list or not parsed_data.data.label_coordinates:
        return ExtractedTextResultOutput(success=False, error="Missing parsed content or coordinates in OmniParser data")

    # Parse coordinates
    coordinates = _parse_coordinates(parsed_data.data.label_coordinates)
    if not coordinates:
        # Warning or error if coordinates couldn't be parsed? For now, proceed without positions.
        pass # Or return ExtractedTextResultOutput(success=False, error="Could not parse coordinates")

    extracted_elements_output: List[ExtractedElementOutput] = []
    lines = parsed_data.data.parsed_content_list.strip().split('\n')

    for line in lines:
        parsed_line = _parse_element_line(line)
        if not parsed_line:
            continue # Skip lines that don't match the expected format

        element_type_parsed, element_id_parsed, text_parsed = parsed_line

        # Apply element type filter if provided
        if element_type_filter and element_type_parsed != element_type_filter:
            continue

        # Get coordinates using the parsed ID
        coords = coordinates.get(element_id_parsed)
        center_x, center_y = (coords[0], coords[1]) if coords and len(coords) >= 2 else (None, None)

        if text_parsed: # Only add elements with non-empty text
            extracted_elements_output.append(
                ExtractedElementOutput(
                    text=text_parsed,
                    position=Position(x=center_x, y=center_y),
                    element_type=element_type_parsed,
                )
            )

    return ExtractedTextResultOutput(
        success=True, element_count=len(extracted_elements_output), extracted_text=extracted_elements_output
    )


# Apply the function_tool decorator to the core logic function
extract_text_from_elements = function_tool(_extract_text_from_elements_core)
