from pathlib import Path
from typing import Optional
import httpx


class ScientificScraper:
    """Downloads remote scientific PDFs with caching and custom headers."""

    def __init__(self, download_dir: Optional[Path] = None):
        if download_dir is None:
            download_dir = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge_base" / "raw"
        self.download_dir = download_dir
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": "DARUKAA-EARTH-Bot/1.0 (Environmental Research Aggregator; contact@darukaa.earth)"
        }

    def fetch_pdf(self, url: str, filename: Optional[str] = None) -> Path:
        """Downloads a PDF from a remote URL and saves it to disk."""
        if not filename:
            filename = url.split("/")[-1].split("?")[0]
            if not filename.endswith(".pdf"):
                filename = f"{filename}.pdf"

        file_path = self.download_dir / filename

        # Return cached file if already downloaded
        if file_path.exists():
            return file_path

        with httpx.Client(headers=self.headers, follow_redirects=True, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()

            # Sanity check for PDF content
            content_type = response.headers.get("content-type", "")
            if "pdf" not in content_type.lower() and not response.content.startswith(b"%PDF"):
                raise ValueError(f"URL {url} did not return a valid PDF response.")

            with open(file_path, "wb") as f:
                f.write(response.content)

        return file_path