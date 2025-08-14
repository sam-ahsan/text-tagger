from app.services.tagging import TaggingService


def test_tagging_service_basic():
    tagger = TaggingService()
    
    texts = ["Elon Musk visited Berlin.", "NVIDIA announced new GPUs."]
    outputs = tagger.tag_texts(texts=texts, language="en", domain_dict=["technology", "AI"])
    assert len(outputs) == 2
    
    tag_0 = outputs[0]
    assert tag_0.text == texts[0]
    assert "elon musk" in tag_0.tags or "Elon Musk" in tag_0.tags
    assert "berlin" in tag_0.tags or "Berlin" in tag_0.tags
    
    tag_1 = outputs[1]
    assert tag_1.text == texts[1]
    assert "technology" in tag_1.tags or "technology" in tag_1.tags
