from transformers import pipeline
from typing import List

class TopicClassifier:
    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        self.pipeline = pipeline("zero-shot-classification", model=model_name)
        self.candidate_labels = [
            "technology", "finance", "sports", "politics", "health", "entertainment"
        ]
    
    def predict(self, texts: List[str]) -> List[str]:
        results = []
        for text in texts:
            output = self.pipeline(text, self.candidate_labels)
            results.append(output["labels"][0])
        return results
