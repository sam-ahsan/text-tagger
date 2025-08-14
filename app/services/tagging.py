import logging
import re
from typing import Dict, List, Optional, Set

from app.models.ner import NERModel
from app.models.topic_classifier import TopicClassifier
from app.schemas.tag import Entity, TagResult, TopicScore

logger = logging.getLogger(__name__)

def _normalize_terms(terms: Optional[List[str]]) -> List[str]:
    if not terms:
        return []
    return sorted({term.strip().lower() for term in terms if term and term.strip()})

def _match_domain_terms(text: str, terms: List[str]) -> Set[str]:
    """
    Word-boundary, case-insensitive matching of provided terms.
    Example: 'AI' matches 'AI systems' but not 'BRAIN'
    """
    if not terms:
        return set()
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, terms)) + r")\b", re.IGNORECASE)
    return {match.group(0).lower() for match in pattern.finditer(text)}

class TaggingService:
    def __init__(self):
        self.ner_model = NERModel()
        self.topic_model = TopicClassifier()
        
        # Fusion tunables
        self.domain_boost = 0.85
        self.ner_weight = 1.0
        self.topic_weight = 1.0

    def tag_texts(
        self, texts: List[str], language: Optional[str] = None, domain_dict: Optional[List[str]] = None
    ) -> List[TagResult]:
        ner_details_per_text = self.ner_model.predict(texts)
        topic_preds_per_text = self.topic_model.predict(texts)

        norm_domain = _normalize_terms(domain_dict)
        
        results = []
        for i, text in enumerate(texts):
            # NER entities
            ner_entities = [Entity(**e) for e in ner_details_per_text[i]]
            ner_labels: Dict[str, float] = {e.text.lower(): e.score * self.ner_weight for e in ner_entities}
            
            # Topics
            topics_raw = topic_preds_per_text[i]
            topic_scores = {t["label"].lower(): t["score"] * self.topic_weight for t in topics_raw}
            topics_structured = [TopicScore(**t) for t in topics_raw] if topics_raw else None
            
            # Domain matches
            domain_hits = _match_domain_terms(text, norm_domain)
            domain_scores = {d: self.domain_boost for d in domain_hits}
            
            # Fusion: max score across sources per label
            combined = {}
            def _acc(key: str, val: float):
                combined[key] = max(combined.get(key, 0.0), val)
            
            for key, value in ner_labels.items():
                _acc(key, value)
            for key, value in topic_scores.items():
                _acc(key, value)
            for key, value in domain_scores.items():
                _acc(key, value)
            
            # Order by score desc, output as display strings
            ordered = sorted(combined.items(), key=lambda kv: kv[1], reverse=True)
            final_tags = [k for k, _ in ordered]
            
            logger.debug(
                f"Text: {text}, NER: {ner_labels}, Topics: {topic_scores}, " \
                f"Domain: {domain_scores}, Combined: {final_tags}"
            )
            
            results.append(TagResult(
                text=text,
                tags=final_tags,
                language=language,
                ner=ner_entities,
                topics=topics_structured
            ))
                    
        return results
