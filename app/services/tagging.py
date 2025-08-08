from typing import List, Optional
from app.models.ner import NERModel
from app.models.topic_classifier import TopicClassifier
from app.schemas.tag import TagResult

import logging
logger = logging.getLogger(__name__)

class TaggingService:
    def __init__(self):
        self.ner_model = NERModel()
        self.topic_model = TopicClassifier()
    
    def tag_texts(
        self, texts: List[str], language: Optional[str] = None, domain_dict: Optional[List[str]] = None
    ) -> List[TagResult]:
        ner_outputs = self.ner_model.predict(texts)
        topic_outputs = self.topic_model.predict(texts)
        
        results = []
        for i, text in enumerate(texts):
            ner_tags = set(ner_outputs[i])
            topic_tag = topic_outputs[i]
            
            domain_tags = set()
            if domain_dict:
                domain_tags = {
                    kw for kw in domain_dict if kw.lower() in text.lower()
                }

            logger.debug(f"Text: {text}, NER Tags: {ner_tags}, Domain Tags: {domain_tags}, Topic Tag: {topic_tag}")

            combined_tags = list(ner_tags | domain_tags | {topic_tag})
            
            results.append(TagResult(
                text=text,
                tags=combined_tags,
                language=language
            ))
        
        return results
