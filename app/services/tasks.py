from typing import List, Optional
from app.workers.celery_app import celery_app
from app.services.tagging import TaggingService

_tagger = TaggingService()

@celery_app.task
def tag_batch_task(
    texts: List[str],
    language: Optional[str] = None,
    domain_dict: Optional[List[str]] = None
):
    """
    Run TaggingService on a batch and return JSON-serializable payload shaped for TagResponse.
    """
    results = _tagger.tag_texts(
        texts=texts,
        language=language,
        domain_dict=domain_dict
    )
    return {"results": [result.model_dump() for result in results]}
