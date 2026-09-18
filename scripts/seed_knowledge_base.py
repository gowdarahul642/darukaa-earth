import json
import sys
from pathlib import Path

# Add app root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.ingestion.arxiv_fetcher import ArxivFetcher
from scripts.ingest_documents import run_ingestion


SEARCH_QUERIES = [
    "soil organic carbon restoration",
    "biodiversity monoculture agriculture",
    "cover crop soil moisture retention",
    "agroforestry ecological interaction"
]


def seed_database():
    base_dir = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"
    manifest_path = base_dir / "manifest.json"

    # Load existing manifest or initialize empty
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            try:
                manifest = json.load(f)
            except json.JSONDecodeError:
                manifest = []
    else:
        manifest = []

    existing_files = {item["file_name"] for item in manifest}
    fetcher = ArxivFetcher()

    print("=== Scraping Scientific Knowledge Base ===")
    for query in SEARCH_QUERIES:
        print(f"\nFetching open-access papers for: '{query}'...")
        results = fetcher.search_and_download(query=query, max_results=2)

        for paper in results:
            if paper["file_name"] not in existing_files:
                manifest.append({
                    "file_name": paper["file_name"],
                    "metadata": paper["metadata"]
                })
                existing_files.add(paper["file_name"])
                print(f"  + Added: {paper['metadata']['title'][:70]}...")

    # Write updated manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\nManifest updated with {len(manifest)} total document(s).")
    print("=== Running Ingestion Pipeline ===")
    run_ingestion()


if __name__ == "__main__":
    seed_database()