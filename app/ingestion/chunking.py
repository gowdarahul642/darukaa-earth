import hashlib
from typing import List
from app.ingestion.schemas import DocumentMetadata, DocumentChunk


class DocumentChunker:
    """Splits text into overlapping chunks aligned to word boundaries."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be strictly smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str, metadata: DocumentMetadata) -> List[DocumentChunk]:
        if not text or len(text.strip()) < 10:
            return []

        chunks: List[DocumentChunk] = []
        start = 0
        text_len = len(text)
        chunk_idx = 0
        doc_hash = hashlib.md5(metadata.title.encode("utf-8")).hexdigest()[:8]

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # Snap end to nearest space to avoid cutting mid-word
            if end < text_len:
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk_content = text[start:end].strip()

            if len(chunk_content) >= 10:
                chunk_id = f"{doc_hash}_{chunk_idx}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_title=metadata.title,
                        chunk_index=chunk_idx,
                        content=chunk_content,
                        char_count=len(chunk_content),
                        metadata=metadata,
                    )
                )
                chunk_idx += 1

            # Advance window
            step = max(1, (end - start) - self.chunk_overlap)
            start += step

            if end == text_len:
                break

        return chunks