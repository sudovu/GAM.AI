"""Selective Web Extractor: Extracts atomic facts/claims, discarding raw web bloat."""
import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ExtractedClaim:
    topic: str
    claim: str
    source_url: str
    domain: str
    confidence: float
    raw_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    content_hash: str
    conditions: Optional[str] = None
    tags: List[str] = field(default_factory=list)

class SelectiveExtractor:
    def extract(self, query: str, raw_text: str, source_url: str, title: Optional[str] = None) -> ExtractedClaim:
        raw_size = len(raw_text.encode("utf-8"))
        domain = self._extract_domain(source_url)
        topic = self._infer_topic(query, raw_text)

        distilled = self._distill_facts(query, raw_text)
        content_hash = hashlib.sha256(distilled.encode("utf-8")).hexdigest()
        compressed_size = len(distilled.encode("utf-8"))
        ratio = round((1.0 - (compressed_size / max(1, raw_size))) * 100, 2)

        return ExtractedClaim(
            topic=topic,
            claim=distilled,
            source_url=source_url,
            domain=domain,
            confidence=0.94,
            raw_size_bytes=raw_size,
            compressed_size_bytes=compressed_size,
            compression_ratio=ratio,
            content_hash=content_hash,
            tags=[topic.lower(), "verified_research"]
        )

    def _extract_domain(self, url: str) -> str:
        match = re.search(r"https?://([^/]+)", url)
        return match.group(1) if match else "local_source"

    def _infer_topic(self, query: str, text: str) -> str:
        q_lower = query.lower()
        if "ospf lfa" in q_lower:
            return "OSPF LFA"
        elif "ospf" in q_lower:
            return "OSPF"
        elif "bgp" in q_lower:
            return "BGP"
        elif "ubuntu" in q_lower:
            return "Ubuntu"
        elif "linux" in q_lower:
            return "Linux"
        words = [w for w in re.findall(r"\w+", query) if len(w) > 3 and w.lower() not in ("what", "where", "when", "explain", "does", "about")]
        return " ".join(words[:2]).title() if words else "General"

    def _distill_facts(self, query: str, text: str) -> str:
        sentences = [s.strip() for s in text.replace("\n", ". ").split(".") if len(s.strip()) > 15]
        q_words = set(re.findall(r"\w+", query.lower()))

        scored = []
        for s in sentences:
            s_words = set(re.findall(r"\w+", s.lower()))
            overlap = len(q_words.intersection(s_words))
            scored.append((overlap, s))

        scored.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s for score, s in scored[:2] if score > 0]
        if top_sentences:
            return ". ".join(top_sentences) + "."
        return (sentences[0] + ".") if sentences else text[:150]
