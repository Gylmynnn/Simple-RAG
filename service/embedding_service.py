from config import client, EMBEDDING_MODEL
from numpy.typing import NDArray
import numpy as np


class EmbeddingService:
    """
    Service for generating vector embeddings from text.

    PURPOSE / TUJUAN:
    - EN: Converts text into dense vector embeddings using an embedding model for semantic search.
    - ID: Mengubah teks menjadi embedding vektor padat menggunakan model embedding untuk pencarian semantik.
    """

    @staticmethod
    def embed(text: str) -> NDArray[np.float64]:
        """
        Generate a vector embedding for the given text.

        PURPOSE / TUJUAN:
        - EN: Calls the embedding API to convert text into a dense vector representation that captures semantic meaning.
        - ID: Memanggil API embedding untuk mengubah teks menjadi representasi vektor padat yang menangkap makna semantik.

        PARAMS / PARAMETER:
        - text (str): Text to embed / Teks untuk di-embed

        RETURNS / HASIL:
        - list[float]: Vector embedding of the text / Embedding vektor teks

        RAISES / MELEMPAR:
        - RuntimeError: If the embedding model doesn't support embeddings or returns no data / Jika model embedding tidak mendukung embedding atau tidak mengembalikan data

        API USED / API YANG DIGUNAKAN:
        - OpenRouter API via OpenAI client / API OpenRouter melalui klien OpenAI
        - Model: EMBEDDING_MODEL (configurable, default: openai/text-embedding-3-small) / Model: EMBEDDING_MODEL (dapat dikonfigurasi, default: openai/text-embedding-3-small)
        - Endpoint: embeddings / Endpoint: embeddings

        PERFORMANCE NOTES / CATATAN PERFORMA:
        - Each call to this function makes an API request / Setiap panggilan ke fungsi ini membuat permintaan API
        - Consider caching embeddings for the same text / Pertimbangkan caching embedding untuk teks yang sama
        - Embedding vectors are typically 1536 dimensions for text-embedding-3-small / Vektor embedding biasanya 1536 dimensi untuk text-embedding-3-small

        EXAMPLE / CONTOH:
        embedding = EmbeddingService.embed("Apa itu AI?")
        # Returns: [0.123, -0.456, 0.789, ...] with 1536 dimensions
        """
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)

        if not response.data:
            raise RuntimeError(
                f"Model embedding '{EMBEDDING_MODEL}' tidak mengembalikan data. "
                "Pastikan model support endpoint embeddings di provider yang dipakai."
            )

        return np.array(response.data[0].embedding, dtype=np.float64)
