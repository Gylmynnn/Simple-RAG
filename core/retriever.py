import re
from dataclasses import dataclass

from service.embedding_service import EmbeddingService
from utils.similarity import cosine_similarity


STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "to",
    "of",
    "in",
    "on",
    "at",
    "for",
    "with",
    "by",
    "from",
    "is",
    "are",
    "was",
    "were",
    "be",
    "what",
    "who",
    "when",
    "where",
    "why",
    "how",
    "today",
    "ini",
    "itu",
    "apa",
    "yang",
    "dan",
    "di",
    "ke",
    "dari",
    "untuk",
    "dengan",
    "pada",
    "adalah",
    "apakah",
    "bisakah",
    "bisa",
}


@dataclass
class RetrievalResult:
    document: str
    score: float
    semantic_score: float
    lexical_score: float
    source_url: str
    title: str


class Retriever:
    def __init__(self, vector_store) -> None:
        self.vector_store = vector_store

    def search(self, query: str, top_k: int = 1, lexical_weight: float = 0.2) -> list[RetrievalResult]:
        if top_k <= 0:
            raise ValueError("top_k harus > 0")
        if not 0 <= lexical_weight <= 1:
            raise ValueError("lexical_weight harus di antara 0.0 sampai 1.0")
        if not self.vector_store.documents:
            return []

        query_embedding = EmbeddingService.embed(query)
        normalized_query = _normalize_text(query)
        query_tokens = _tokenize(normalized_query)

        results: list[RetrievalResult] = []
        for document, embedding in zip(self.vector_store.documents, self.vector_store.embeddings):
            semantic_score = float(cosine_similarity(query_embedding, embedding))
            lexical_score = _lexical_score(query_tokens, normalized_query, document)
            score = (1 - lexical_weight) * semantic_score + lexical_weight * lexical_score

            source_url = _extract_metadata_value(document, "Sumber")
            title = _extract_metadata_value(document, "Judul")
            results.append(
                RetrievalResult(
                    document=document,
                    score=score,
                    semantic_score=semantic_score,
                    lexical_score=lexical_score,
                    source_url=source_url,
                    title=title,
                )
            )

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-zA-Z0-9]+", text.lower())
        if len(token) >= 2 and token not in STOPWORDS
    }


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _lexical_score(query_tokens: set[str], normalized_query: str, document: str) -> float:
    if not query_tokens:
        return 0.0

    normalized_document = _normalize_text(document)
    doc_tokens = _tokenize(normalized_document)
    if not doc_tokens:
        return 0.0

    intersection = len(query_tokens & doc_tokens)
    coverage = intersection / len(query_tokens)

    phrase_bonus = 0.0
    if len(normalized_query) >= 16 and normalized_query in normalized_document:
        phrase_bonus = 0.2

    return min(1.0, coverage + phrase_bonus)


def _extract_metadata_value(document: str, key: str) -> str:
    prefix = f"{key}:"
    for line in document.splitlines()[:8]:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""
