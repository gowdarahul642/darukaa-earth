from pathlib import Path
from typing import Tuple
import fitz  # PyMuPDF


class DocumentLoader:
    """Loads text from local files (.pdf, .txt, .md)."""

    @staticmethod
    def load_file(file_path: Path) -> Tuple[str, int]:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            return DocumentLoader._load_pdf(file_path)
        elif suffix in [".txt", ".md"]:
            return DocumentLoader._load_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    @staticmethod
    def _load_pdf(file_path: Path) -> Tuple[str, int]:
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            text_pages = []

            for page in doc:
                text = page.get_text("text")
                if text:
                    text_pages.append(text)

            doc.close()
            full_text = "\n\n".join(text_pages)

            if not full_text.strip():
                raise ValueError(f"No extractable text found in PDF: {file_path.name}. (Might be scanned image)")

            return full_text, page_count
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF {file_path.name}: {str(e)}")

    @staticmethod
    def _load_text(file_path: Path) -> Tuple[str, int]:
        encodings = ["utf-8", "latin-1", "cp1252"]
        for enc in encodings:
            try:
                content = file_path.read_text(encoding=enc)
                return content, 1
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Could not decode text file {file_path.name} with standard encodings.")