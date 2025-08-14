from typing import List

from transformers import pipeline


class TopicClassifier:
    def __init__(self, labels: List[str] | None = None, model_name: str = "facebook/bart-large-mnli"):
        self.labels = labels or [
            "technology", "business", "entertainment", "sports", "politics", "food", "pop culture",
            "science", "health", "finance", "gaming", "travel", "education", "music"
        ]
        self.pipeline = pipeline("zero-shot-classification", model=model_name)
        
        # Tunable
        self.threshold = 0.7
        self.top_k = 5

    def predict(self, texts: List[str]) -> List[str]:
        """
        Returns for each text a list of {label, score} dicts, sorted by score descending and
        filtered by threshold, capped to top_k. Multi-label enabled.
        """
        outputs = self.pipeline(texts, candidate_labels=self.labels, multi_label=True)
        if isinstance(texts, str):
            outputs = [outputs]
        
        results = []
        for output in outputs:
            pairs = list(zip(output["labels"], output["scores"]))
            pairs.sort(key=lambda x: x[1], reverse=True)
            filtered = [{"label": label, "score": float(score)} for label, score in pairs if score >= self.threshold]
            results.append(filtered[:self.top_k])
        return results
