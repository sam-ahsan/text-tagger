from fastapi import APIRouter, HTTPException
from app.schemas.tag import TagRequest, TagResponse, TagResult
from app.services.tagging import TaggingService

router = APIRouter()
tagger = TaggingService()

@router.post("/tag", response_model=TagResponse)
def tag_text(payload: TagRequest):
    if not payload.texts:
        raise HTTPException(status_code=400, detail="No input texts provided for tagging.")
    
    results = tagger.tag_texts(
        texts=payload.texts,
        language=payload.language,
        domain_dict=payload.domain_dict
    )
    
    return TagResponse(results=results)
