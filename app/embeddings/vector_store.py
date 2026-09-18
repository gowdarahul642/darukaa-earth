from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from app.ingestion.schemas import DocumentChunk


class VectorStoreManager:
    """Manages embedding generation and vector storage in ChromaDB."""

    def __init__(
        self,
        collection_name: str = "environmental_knowledge",
        persist_dir: Optional[Path] = None,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        if persist_dir is None:
            try:
                from app.config import settings
                persist_dir = settings.data_dir / "chroma"
            except (ImportError, AttributeError):
                # Fallback path if settings import is unavailable
                persist_dir = Path(__file__).resolve().parent.parent.parent / "data" / "chroma"

        persist_dir.mkdir(parents=True, exist_ok=True)

        self.persist_dir = persist_dir
        self.collection_name = collection_name

        # Initialize ChromaDB Persistent Client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
        )

        # Initialize SentenceTransformer embedding engine
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # Get or create vector collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates dense vector embeddings for a batch of text strings."""
        if not texts:
            return []
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Embeds and upserts DocumentChunk objects into ChromaDB."""
        if not chunks:
            return 0

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)

            # Flatten metadata dict for ChromaDB storage compatibility
            meta = chunk.metadata.model_dump()
            meta["chunk_index"] = chunk.chunk_index
            meta["document_title"] = chunk.document_title

            # Convert non-primitive types for Chroma metadata compliance
            for key, val in meta.items():
                if isinstance(val, list):
                    meta[key] = ",".join(str(v) for v in val)
                elif val is None:
                    meta[key] = ""
                elif not isinstance(val, (str, int, float, bool)):
                    meta[key] = str(val)

            metadatas.append(meta)

        embeddings = self.generate_embeddings(documents)

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return len(ids)

    def query_similar(
        self, query_text: str, top_k: int = 5, where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Queries the vector index for semantically similar chunks with optional metadata filtering."""
        query_embedding = self.generate_embeddings([query_text])[0]

        query_kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
        }

        if where_filter:
            query_kwargs["where"] = where_filter

        results = self.collection.query(**query_kwargs)

        extracted_results = []
        if results and results.get("documents"):
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

            for doc_id, doc, meta, dist in zip(ids, docs, metas, distances):
                extracted_results.append(
                    {
                        "chunk_id": doc_id,
                        "content": doc,
                        "metadata": meta,
                        "similarity_score": round(1.0 - float(dist), 4),
                    }
                )

        return extracted_results

    def count(self) -> int:
        """Returns total records in the collection."""
        return self.collection.count()