from app.services.tagging import TaggingService

def test_tagging_basic():
    tagger = TaggingService()
    texts = ["Barack Obama visited Berlin."]
    result = tagger.tag_texts(texts)
    
    assert result[0].text == texts[0]
    assert isinstance(result[0].tags, list)
    assert len(result[0].tags) > 0