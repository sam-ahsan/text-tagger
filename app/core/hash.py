import hashlib
import json
from typing import Any, Dict, List, Optional


def normalize_payload(
    *, texts: List[str], language: Optional[str], domain_dict: Optional[List[str]]
) -> Dict[str, Any]:
    norm_texts = [text.strip() for text in texts]
    norm_lang = language.lower().strip() if language else None
    norm_domain = sorted({kw.strip() for kw in (domain_dict or [])})
    return {
        "texts": norm_texts,
        "language": norm_lang,
        "domain_dict": norm_domain
    }

def payload_hash(payload: Dict[str, Any]) -> str:
    s = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
