from pydantic import BaseModel, Field
from typing import Annotated, List, Optional
from enum import Enum

SmallBatch = Annotated[List[str], Field(min_length=1, max_items=1000)]

class JobStatus(str, Enum):
    PENDING="PENDING";
    STARTED="STARTED";
    RETRY="RETRY";
    FAILURE="FAILURE";
    SUCCESS="SUCCESS";

class ErrorInfo(BaseModel):
    code: str
    message: str

class TagRequest(BaseModel):
    texts: SmallBatch = Field(
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

class Entity(BaseModel):
    text: str = Field(..., description="The surface form of the entity")
    label: str = Field(..., description="Entity type label, e.g. PER/ORG/LOC/MISC")
    score: float = Field(..., ge=0.0, le=1.0, description="Model confidence for this entity")

class TagResult(BaseModel):
    model_config = {"extra": "forbid"}
    text: str
    tags: List[str]
    language: Optional[str] = None
    ner: Optional[List[Entity]] = None

class TagResponse(BaseModel):
    results: List[TagResult]
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "results": [{
                    "text": "Elon Musk visited Berlin.",
                    "tags": ["ORG", "LOC"],
                    "language": "en",
                    "ner": [{
                        "text": "Elon Musk",
                        "label": "ORG",
                        "score": 0.99
                    }, {
                        "text": "Berlin",
                        "label": "LOC",
                        "score": 0.98
                    }]
                }]
            }]
        }
    }

class BatchSubmitResponse(BaseModel):
    job_id: str

class BatchStatusResponse(BaseModel):
    status: JobStatus
    result: Optional[TagResponse] = None
    error: Optional[ErrorInfo] = None
