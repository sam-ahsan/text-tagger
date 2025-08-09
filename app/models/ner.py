from transformers import pipeline
from typing import List, Dict

def _clean_word(word: str) -> str:
    word = word.replace("##", "")
    return " ".join(word.split())

class NERModel:
    def __init__(self, model_name: str = "dslim/bert-base-NER"):
        self.pipeline = pipeline(
            task="token-classification",
            model=model_name,
            aggregation_strategy="simple"
        )

    def predict(self, texts: List[str]) -> List[List[Dict]]:
        results = []
        for text in texts:
            entities = self.pipeline(text)
            details: List[Dict] = []
            for entity in entities:
                word = _clean_word(entity.get("word", "").strip())
                if word:
                    details.append({
                        "text": word,
                        "label": entity.get("entity_group", ""),
                        "score": float(entity.get("score", 0.0))
                    })
            results.append(details)
        return results
