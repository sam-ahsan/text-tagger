from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class TagRequest(BaseModel):
    texts: List[str] = Field(..., description="List of input texts to tag")
    domain_dict: Optional[List[str]] = Field(
        None, description="Optional list of domain-specific keywords to bias tagging"
    )
    language: Optional[str] = Field(
        None, description="Optional hint for language (e.g., 'en', 'fr')"
    )

class TagResult(BaseModel):
    text: str
    tags: List[str]
    language: Optional[str] = None

class TagResponse(BaseModel):
    results: List[TagResult]
