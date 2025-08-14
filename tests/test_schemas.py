from pydantic import ValidationError
from app.schemas.tag import TagRequest

def test_tag_request_validation_ok():
    request = TagRequest(texts=["hello", "world"])
    assert request.texts == ["hello", "world"]

def test_tag_request_validation_empty_fails():
    try:
        TagRequest(texts=[])
        assert False, "Should have raised"
    except Exception as e:
        assert isinstance(e, ValidationError)
