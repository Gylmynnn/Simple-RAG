from config import client, EMBEDDING_MODEL


class EmbeddingService:
    @staticmethod
    def embed(text: str) -> list[float]:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)

        if not response.data:
            raise RuntimeError(
                f"Model embedding '{EMBEDDING_MODEL}' tidak mengembalikan data. "
                "Pastikan model support endpoint embeddings di provider yang dipakai."
            )

        return response.data[0].embedding
