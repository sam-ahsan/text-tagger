from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Entity(BaseModel):
    text: str = Field(..., description="The surface form of the entity")
    label: str = Field(..., description="Entity type label, e.g. PER/ORG/LOC/MISC")
    score: float = Field(..., ge=0.0, le=1.0, description="Model confidence for this entity")

class TagRequest(BaseModel):
    texts: List[str] = Field(
        ...,
        description="List of input texts to tag",
        examples=[["Elon Musk visited Berlin.", "NVIDIA announced new GPUs."]]
    )
    language: Optional[str] = Field(
        None,
        description="Optional hint for language (e.g., 'en', 'fr')",
        examples=["en", "fr", "de"]
    )
    domain_dict: Optional[List[str]] = Field(
        None,
        description="Optional list of domain-specific keywords to bias tagging",
        examples=[["technology", "AI", "NVIDIA"]]
    )

class TagResult(BaseModel):
    text: str
    tags: List[str]
    language: Optional[str] = None
    ner: Optional[List[Entity]] = None

class TagResponse(BaseModel):
    results: List[TagResult]

class BatchSubmitResponse(BaseModel):
    job_id: str

class BatchStatusResponse(BaseModel):
    status: str # PENDING | STARTED | RETRY | FAILURE | SUCCESS
    result: Optional[TagResponse] = None
    error: Optional[str] = None
