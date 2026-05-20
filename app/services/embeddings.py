from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL_NAME


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding.tolist()
