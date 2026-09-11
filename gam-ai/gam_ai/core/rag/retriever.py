"""RAG Retriever: Seamlessly queries both document chunks and verified knowledge items."""
from typing import List, Dict, Any, Optional
from gam_ai.core.database.db import DatabaseManager
from gam_ai.core.rag.indexer import LightweightSemanticIndexer

class LocalRetriever:
    def __init__(self, db: DatabaseManager, indexer: Optional[LightweightSemanticIndexer] = None):
        self.db = db
        self.indexer = indexer or LightweightSemanticIndexer()

    def retrieve_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        sql = """
        SELECT c.id, c.content, d.file_name, d.file_path
        FROM document_chunks c
        JOIN document_references d ON c.doc_id = d.id
        LIMIT 50;
        """
        cursor = self.db.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            return []

        doc_tuples = [(r["id"], r["content"]) for r in rows]
        ranked = self.indexer.rank_documents(query, doc_tuples, top_k=top_k)

        results = []
        row_map = {r["id"]: r for r in rows}
        for chunk_id, text, score in ranked:
            r = row_map[chunk_id]
            results.append({
                "chunk_id": chunk_id,
                "content": text,
                "source": r["file_name"],
                "score": round(score, 3)
            })
        return results
