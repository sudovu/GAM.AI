"""Compact lightweight semantic indexer: zero heavy ML runtime dependency."""
import math
import re
from typing import List, Dict, Tuple

class LightweightSemanticIndexer:
    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b\w{2,}\b", text)]

    def compute_similarity(self, query: str, document: str) -> float:
        q_tokens = self._tokenize(query)
        d_tokens = self._tokenize(document)
        if not q_tokens or not d_tokens:
            return 0.0

        q_counts: Dict[str, int] = {}
        for t in q_tokens:
            q_counts[t] = q_counts.get(t, 0) + 1

        d_counts: Dict[str, int] = {}
        for t in d_tokens:
            d_counts[t] = d_counts.get(t, 0) + 1

        dot_product = sum(q_counts[t] * d_counts.get(t, 0) for t in q_counts)
        q_norm = math.sqrt(sum(v * v for v in q_counts.values()))
        d_norm = math.sqrt(sum(v * v for v in d_counts.values()))

        if q_norm == 0 or d_norm == 0:
            return 0.0
        return dot_product / (q_norm * d_norm)

    def rank_documents(self, query: str, documents: List[Tuple[str, str]], top_k: int = 3) -> List[Tuple[str, str, float]]:
        scored = []
        for doc_id, text in documents:
            sim = self.compute_similarity(query, text)
            if sim > 0.05:
                scored.append((doc_id, text, sim))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]
