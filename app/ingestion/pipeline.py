from pathlib import Path
from typing import List, Dict, Any, Tuple
from app.ingestion.schemas import DocumentMetadata, DocumentChunk, IngestionResult
from app.ingestion.loaders import DocumentLoader
from app.ingestion.cleaning import TextCleaner
from app.ingestion.chunking import DocumentChunker


class IngestionPipeline:
    """Complete document ingestion pipeline for DARUKAA.EARTH."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.loader = DocumentLoader()
        self.cleaner = TextCleaner()
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def process_file(self, file_path: Path, metadata_dict: Dict[str, Any]) -> Tuple[IngestionResult, List[DocumentChunk]]:
        try:
            metadata = DocumentMetadata(**metadata_dict)
            raw_text, total_pages = self.loader.load_file(file_path)
            cleaned_text = self.cleaner.clean_text(raw_text)
            chunks = self.chunker.chunk_text(cleaned_text, metadata)

            if not chunks:
                return IngestionResult(
                    document_title=metadata.title,
                    total_pages=total_pages,
                    total_chunks=0,
                    status="failed",
                    error="Document produced zero valid chunks after cleaning"
                ), []

            return IngestionResult(
                document_title=metadata.title,
                total_pages=total_pages,
                total_chunks=len(chunks),
                status="success"
            ), chunks

        except Exception as e:
            return IngestionResult(
                document_title=str(metadata_dict.get("title", file_path.name)),
                total_pages=0,
                total_chunks=0,
                status="failed",
                error=str(e)
            ), []