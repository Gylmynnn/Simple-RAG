from service.embedding_service import EmbeddingService


class VectorStore:
    def __init__(self, documents: list[str]) -> None:
        self.documents = documents
        self.embeddings = [EmbeddingService.embed(doc) for doc in documents]
