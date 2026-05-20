from app.services.chunk_registry import (
    detect_file_hints,
    keyword_search_chunks,
    search_chunks_by_file_name,
)
from app.services.vector_store import VectorStore


class RetrievalService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def retrieve(
        self,
        repo_id: str,
        query: str,
        query_embedding: list[float],
        semantic_top_k: int = 5,
        keyword_top_k: int = 8,
        file_hint_top_k: int = 5,
        max_total: int = 12,
    ) -> list[dict]:
        file_results = search_chunks_by_file_name(
            repo_id=repo_id,
            file_name_markers=detect_file_hints(query),
            top_k=file_hint_top_k,
        )
        semantic_results = self.vector_store.search(
            repo_id=repo_id,
            query_embedding=query_embedding,
            top_k=semantic_top_k,
        )
        keyword_results = keyword_search_chunks(
            repo_id=repo_id,
            query=query,
            top_k=keyword_top_k,
        )

        return deduplicate_chunks(file_results + keyword_results + semantic_results)[:max_total]


def deduplicate_chunks(chunks: list[dict]) -> list[dict]:
    result = []
    seen = set()

    for chunk in chunks:
        key = (chunk["file_path"], chunk["chunk_index"])

        if key in seen:
            continue

        seen.add(key)
        result.append(chunk)

    return result
