from transformers import pipeline
from typing import List, Dict

class NERModel:
    def __init__(self, model_name: str = "dslim/bert-base-NER"):
        self.pipeline = pipeline("ner", model=model_name, grouped_entities=True)
    
    def predict(self, texts: List[str]) -> List[List[str]]:
        results = []
        for text in texts:
            entities = self.pipeline(text)
            tags = [entity["word"] for entity in entities]
            results.append(tags)
        return results
