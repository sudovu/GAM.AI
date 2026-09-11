"""DocumentProcessor: Ingests documents by reference, extracts text, chunks, and prunes raw copies."""
import os
import hashlib
import uuid
from typing import List, Dict, Any
from gam_ai.core.database.db import DatabaseManager

class DocumentProcessor:
    def __init__(self, db: DatabaseManager, chunk_size_words: int = 150):
        self.db = db
        self.chunk_size_words = chunk_size_words

    def _compute_file_hash(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def process_file(self, file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        file_hash = self._compute_file_hash(file_path)
        file_name = os.path.basename(file_path)
        doc_id = hashlib.md5(file_path.encode("utf-8")).hexdigest()

        text = self._extract_text(file_path)
        chunks = self._create_chunks(text)

        sql_doc = """
        INSERT INTO document_references (id, file_path, file_name, file_size_bytes, file_hash, indexed_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(file_path) DO UPDATE SET
            file_hash = excluded.file_hash,
            file_size_bytes = excluded.file_size_bytes,
            indexed_at = CURRENT_TIMESTAMP;
        """
        self.db.execute(sql_doc, (doc_id, os.path.abspath(file_path), file_name, file_size, file_hash))
        self.db.execute("DELETE FROM document_chunks WHERE doc_id = ?", (doc_id,))

        chunk_records = []
        for idx, chunk_str in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            chunk_hash = hashlib.sha256(chunk_str.encode("utf-8")).hexdigest()
            token_count = len(chunk_str.split())
            chunk_records.append((chunk_id, doc_id, idx, chunk_str, chunk_hash, token_count))

        sql_chunk = """
        INSERT INTO document_chunks (id, doc_id, chunk_index, content, content_hash, token_count)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        self.db.executemany(sql_chunk, chunk_records)
        self.db.commit()

        return {
            "doc_id": doc_id,
            "file_name": file_name,
            "chunks_indexed": len(chunks),
            "file_size_bytes": file_size
        }

    def _extract_text(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".txt", ".md", ".py", ".sh", ".json", ".yaml", ".yml", ".c", ".h", ".cpp"):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(path)
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(pages)
            except Exception as e:
                return f"[PDF extraction fallback: {e}]"
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    def _create_chunks(self, text: str) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks = []
        for i in range(0, len(words), self.chunk_size_words):
            chunk = " ".join(words[i:i + self.chunk_size_words])
            chunks.append(chunk)
        return chunks
