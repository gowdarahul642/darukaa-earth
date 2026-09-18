import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import httpx
from app.ingestion.scraper import ScientificScraper


class ArxivFetcher:
    """Queries arXiv open API for environmental research papers and downloads PDFs."""

    ARXIV_API_URL = "https://export.arxiv.org/api/query"

    def __init__(self, scraper: Optional[ScientificScraper] = None):
        self.scraper = scraper or ScientificScraper()

    def search_and_download(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Searches arXiv for a query string and downloads available open-access PDFs."""
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }

        with httpx.Client(timeout=20.0) as client:
            res = client.get(self.ARXIV_API_URL, params=params)
            res.raise_for_status()

        root = ET.fromstring(res.text)
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        downloaded_papers = []

        for entry in root.findall("atom:entry", namespace):
            title = entry.find("atom:title", namespace).text.strip().replace("\n", " ")
            published = entry.find("atom:published", namespace).text[:4]
            paper_id = entry.find("atom:id", namespace).text.split("/")[-1]

            pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
            filename = f"arxiv_{paper_id.replace('.', '_')}.pdf"

            try:
                file_path = self.scraper.fetch_pdf(pdf_url, filename=filename)

                metadata = {
                    "title": title,
                    "source": "arXiv Preprints",
                    "organization": "arXiv",
                    "publication_year": int(published),
                    "url": f"https://arxiv.org/abs/{paper_id}",
                    "topic": query,
                    "environmental_metrics": [
                        "soil_organic_carbon",
                        "biodiversity",
                        "species_richness"
                    ],
                    "geographic_scope": "Global",
                    "document_type": "research"
                }

                downloaded_papers.append({
                    "file_name": filename,
                    "file_path": file_path,
                    "metadata": metadata
                })
            except Exception:
                continue

        return downloaded_papers