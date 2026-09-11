"""WebResearchEngine: Implements cache-first research, selective extraction, and minimal metadata."""
import hashlib
from typing import Optional, Dict, Any, List
from gam_ai.interfaces.search import ISearchProvider, SearchResultItem
from gam_ai.core.cache.smart_cache import SmartCacheManager
from gam_ai.core.research.extractor import SelectiveExtractor, ExtractedClaim
from gam_ai.core.database.db import DatabaseManager

class MockOfflineSearchProvider(ISearchProvider):
    def is_available(self) -> bool:
        return True

    def search(self, query: str, max_results: int = 2) -> List[SearchResultItem]:
        q_lower = query.lower()
        if "ospf lfa" in q_lower or "loop-free alternate" in q_lower:
            return [
                SearchResultItem(
                    title="RFC 5286 - Basic Specification for IP Fast Reroute: Loop-Free Alternates",
                    url="https://datatracker.ietf.org/doc/html/rfc5286",
                    domain="ietf.org",
                    snippet="OSPF Loop-Free Alternate (LFA) provides fast reroute for IP traffic upon link or node failure.",
                    raw_content=(
                        "RFC 5286 describes IP Fast Reroute using Loop-Free Alternates (LFA). "
                        "OSPF LFA computes a loop-free backup next-hop path in advance of network topology failure. "
                        "When a link failure occurs, traffic is instantly switched to the LFA next-hop within sub-50ms. "
                        "This eliminates micro-loops and minimizes packet loss during IGP convergence."
                    )
                )
            ]
        elif "ospf hello" in q_lower:
            return [
                SearchResultItem(
                    title="Cisco OSPF Configuration Guide - Hello and Dead Timers",
                    url="https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13689-1.html",
                    domain="cisco.com",
                    snippet="The default OSPF hello interval is 10 seconds for broadcast and point-to-point networks.",
                    raw_content=(
                        "On broadcast and point-to-point network types like Ethernet, OSPF defaults to a 10-second hello interval "
                        "and a 40-second dead interval. On non-broadcast multi-access (NBMA) networks, the hello interval defaults to 30 seconds."
                    )
                )
            ]
        elif "bgp local preference" in q_lower:
            return [
                SearchResultItem(
                    title="RFC 4271 - A Border Gateway Protocol 4 (BGP-4)",
                    url="https://datatracker.ietf.org/doc/html/rfc4271",
                    domain="ietf.org",
                    snippet="BGP LOCAL_PREF is a well-known discretionary attribute distributed throughout an autonomous system.",
                    raw_content=(
                        "The LOCAL_PREF attribute is an attribute that is included in all BGP UPDATE messages "
                        "sent to internal peers. It informs other internal routers within the AS of the advertising router's "
                        "preference for an advertised route. Higher LOCAL_PREF values are prioritized over lower values."
                    )
                )
            ]
        return [
            SearchResultItem(
                title=f"Technical Reference: {query}",
                url="https://docs.example.org/reference",
                domain="example.org",
                snippet=f"Factual technical summary regarding {query}.",
                raw_content=f"Technical specification and verified details for {query}."
            )
        ]

class WebResearchEngine:
    def __init__(
        self,
        db: DatabaseManager,
        cache: SmartCacheManager,
        search_provider: Optional[ISearchProvider] = None,
        extractor: Optional[SelectiveExtractor] = None
    ):
        self.db = db
        self.cache = cache
        self.search_provider = search_provider or MockOfflineSearchProvider()
        self.extractor = extractor or SelectiveExtractor()

    def record_query(self, query: str) -> int:
        q_norm = query.strip().lower()
        q_hash = hashlib.sha256(q_norm.encode("utf-8")).hexdigest()

        sql = """
        INSERT INTO query_history (query_hash, query_text, first_seen, last_seen, frequency)
        VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
        ON CONFLICT(query_hash) DO UPDATE SET
            last_seen = CURRENT_TIMESTAMP,
            frequency = query_history.frequency + 1;
        """
        self.db.execute(sql, (q_hash, q_norm))
        self.db.commit()

        row = self.db.execute("SELECT frequency FROM query_history WHERE query_hash = ?", (q_hash,)).fetchone()
        return row["frequency"] if row else 1

    def get_query_frequency(self, query: str) -> int:
        q_norm = query.strip().lower()
        q_hash = hashlib.sha256(q_norm.encode("utf-8")).hexdigest()
        row = self.db.execute("SELECT frequency FROM query_history WHERE query_hash = ?", (q_hash,)).fetchone()
        return row["frequency"] if row else 0

    def research(self, query: str, force_refresh: bool = False) -> Dict[str, Any]:
        cache_key = f"research:{query.strip().lower()}"

        if not force_refresh:
            cached = self.cache.get(cache_key)
            if cached:
                return {
                    "source": "cache",
                    "hit": True,
                    "content": cached["content"],
                    "cache_id": cached["id"],
                    "access_count": cached["access_count"]
                }

        results = self.search_provider.search(query, max_results=1)
        if not results:
            return {"source": "none", "hit": False, "content": "No results found."}

        top_result = results[0]
        raw_text = top_result.raw_content or top_result.snippet
        extracted = self.extractor.extract(query, raw_text, top_result.url, top_result.title)

        self._record_source(top_result, extracted)

        cache_id = self.cache.set(
            key=cache_key,
            content=extracted.claim,
            ttl_seconds=3600,
            priority=1,
            source=top_result.url,
            category="web_research"
        )

        return {
            "source": "web_research",
            "hit": False,
            "topic": extracted.topic,
            "content": extracted.claim,
            "confidence": extracted.confidence,
            "source_url": extracted.source_url,
            "domain": extracted.domain,
            "raw_size_bytes": extracted.raw_size_bytes,
            "compressed_size_bytes": extracted.compressed_size_bytes,
            "compression_ratio": extracted.compression_ratio,
            "cache_id": cache_id
        }

    def _record_source(self, result: SearchResultItem, claim: ExtractedClaim) -> None:
        sql = """
        INSERT INTO sources (id, url, domain, title, quality_score, retrieved_at, last_verified_at, content_hash)
        VALUES (?, ?, ?, ?, 0.9, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
        ON CONFLICT(url) DO UPDATE SET
            last_verified_at = CURRENT_TIMESTAMP;
        """
        source_id = hashlib.md5(result.url.encode("utf-8")).hexdigest()
        self.db.execute(sql, (source_id, result.url, result.domain, result.title, claim.content_hash))
        self.db.commit()
