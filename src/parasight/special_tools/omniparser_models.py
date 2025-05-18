from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OmniParserData(BaseModel):
    """Data structure for OmniParser results."""
    parsed_content_list: str
    # Add other fields as needed based on actual OmniParser output structure


class OmniParserResultInput(BaseModel):
    """Input model for OmniParser analysis results."""
    success: bool
    data: Optional[OmniParserData] = None
    error: Optional[str] = None
