import json
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.ingestion.schemas import DocumentChunk
from app.embeddings.vector_store import VectorStoreManager


def index_knowledge_base():
    processed_json = Path(__file__).resolve().parent.parent / "data" / "knowledge_base" / "processed" / "ingested_chunks.json"

    if not processed_json.exists():
        print(f"Error: Ingested chunks file not found at {processed_json}.")
        print("Please run 'py scripts/seed_knowledge_base.py' first.")
        return

    with open(processed_json, "r", encoding="utf-8") as f:
        raw_chunks = json.load(f)

    chunks = [DocumentChunk(**item) for item in raw_chunks]
    print(f"Loaded {len(chunks)} chunk(s) from processed storage.")

    print("Initializing VectorStoreManager (loading MiniLM model & ChromaDB)...")
    vector_manager = VectorStoreManager()

    print("Generating embeddings and indexing into ChromaDB...")
    added_count = vector_manager.add_chunks(chunks)

    print(f" Successfully indexed {added_count} chunk(s) into ChromaDB!")
    print(f"Total documents in collection '{vector_manager.collection_name}': {vector_manager.count()}")


if __name__ == "__main__":
    index_knowledge_base()