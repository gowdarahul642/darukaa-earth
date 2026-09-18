import json
import sys
from pathlib import Path

# Add app root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.ingestion.pipeline import IngestionPipeline


def run_ingestion():
    base_dir = Path(__file__).resolve().parent.parent / "data" / "knowledge_base"
    manifest_path = base_dir / "manifest.json"
    raw_dir = base_dir / "raw"
    processed_dir = base_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    if not manifest_path.exists():
        print(f"Error: Manifest file not found at {manifest_path}")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    pipeline = IngestionPipeline(chunk_size=1000, chunk_overlap=200)
    all_chunks = []

    print(f"Starting ingestion process for {len(manifest)} documents...")

    for entry in manifest:
        file_name = entry.get("file_name")
        file_path = raw_dir / file_name
        metadata = entry.get("metadata", {})

        print(f"\nProcessing: {file_name}...")
        result, chunks = pipeline.process_file(file_path, metadata)

        if result.status == "success":
            print(f"  ✓ Success: {result.total_chunks} chunks generated from {result.total_pages} page(s).")
            all_chunks.extend([c.model_dump() for c in chunks])
        else:
            print(f"  ✗ Failed: {result.error}")

    # Save output chunks for Phase 4 ChromaDB loading
    output_file = processed_dir / "ingested_chunks.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\nIngestion Complete! Total {len(all_chunks)} chunks saved to {output_file}")


if __name__ == "__main__":
    run_ingestion()