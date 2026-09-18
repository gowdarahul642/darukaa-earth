import pytest
from unittest.mock import MagicMock, patch
from app.ingestion.scraper import ScientificScraper
from app.ingestion.arxiv_fetcher import ArxivFetcher


@patch("httpx.Client.get")
def test_scraper_fetch_pdf(mock_get, tmp_path):
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.headers = {"content-type": "application/pdf"}
    mock_res.content = b"%PDF-1.4 Mock Scientific Content"
    mock_get.return_value = mock_res

    scraper = ScientificScraper(download_dir=tmp_path)
    path = scraper.fetch_pdf("https://example.org/sample.pdf")

    assert path.exists()
    assert path.name == "sample.pdf"


def test_arxiv_fetcher_init():
    fetcher = ArxivFetcher()
    assert "arxiv.org" in fetcher.ARXIV_API_URL