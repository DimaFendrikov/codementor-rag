import chromadb

from app.config import CHROMA_COLLECTION_NAME, VECTOR_DB_DIR


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        self.collection = self.client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

    def clear_repository(self, repo_id: str) -> None:
        try:
            self.collection.delete(where={"repo_id": repo_id})
        except Exception:
            return

    def add_chunks(self, repo_id: str, chunks: list[dict], embeddings: list[list[float]]) -> None:
        if not chunks:
            return

        ids = []
        documents = []
        metadatas = []

        for index, chunk in enumerate(chunks):
            ids.append(f"{repo_id}::{chunk['file_path']}::{chunk['chunk_index']}::{index}")
            documents.append(chunk["content"])
            metadatas.append(
                {
                    "repo_id": repo_id,
                    "file_path": chunk["file_path"],
                    "chunk_index": chunk["chunk_index"],
                    "chunk_type": chunk.get("chunk_type") or "text",
                    "symbol_name": chunk.get("symbol_name") or "",
                }
            )

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def search(self, repo_id: str, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"repo_id": repo_id},
        )

        found_chunks = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for document, metadata, distance in zip(documents, metadatas, distances):
            found_chunks.append(
                {
                    "repo_id": metadata["repo_id"],
                    "file_path": metadata["file_path"],
                    "chunk_index": metadata["chunk_index"],
                    "chunk_type": metadata.get("chunk_type", "text"),
                    "symbol_name": metadata.get("symbol_name", ""),
                    "content": document,
                    "distance": distance,
                }
            )

        return found_chunks
