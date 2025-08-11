import string

from transformers import pipeline
from typing import List, Dict

class NERModel:
    def __init__(self, model_name: str = "dslim/bert-base-NER"):
        self.pipeline = pipeline(
            task="token-classification",
            model=model_name,
            aggregation_strategy="simple"
        )
        self.min_score = 0.6
        self.min_len = 2
    
    def _clean_text(self, s: str) -> str:
        s = s.strip().strip(string.punctuation + "“”‘’")
        return " ".join(s.split())

    def predict(self, texts: List[str]) -> List[List[Dict]]:
        if isinstance(texts, str):
            texts = [texts]
        
        raw = self.pipeline(texts)
        if isinstance(raw, dict):
            raw = [raw]
        
        results = []
        for entities in raw:
            cleaned = []
            for entity in entities:
                # entity = {'entity_group': 'ORG', 'word': 'NVIDIA', 'score': 0.99, 'start':..,'end':..}
                text = self._clean_text(entity.get("word") or entity.get("entity") or "")
                if not text or len(text.replace("#", "")) < self.min_len:
                    continue
                score = float(entity.get("score", 0.0))
                if score < self.min_score:
                    continue
                label = entity.get("entity_group") or entity.get("entity") or "MISC"
                cleaned.append({"text": text, "label": label, "score": score})
            results.append(cleaned)
        return results
