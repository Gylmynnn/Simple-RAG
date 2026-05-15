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
    """
    Retriever for semantic and lexical search over documents.
    
    PURPOSE / TUJUAN:
    - EN: Performs hybrid search combining semantic (embedding-based) and lexical (keyword-based) matching to find relevant documents.
    - ID: Melakukan pencarian hibrida yang menggabungkan pencocokan semantik (berbasis embedding) dan leksikal (berbasis kata kunci) untuk menemukan dokumen yang relevan.
    """
    
    def __init__(self, vector_store) -> None:
        """
        Initialize the retriever with a vector store.
        
        PURPOSE / TUJUAN:
        - EN: Sets up the retriever with a reference to the vector store containing documents and embeddings.
        - ID: Menyiapkan retriever dengan referensi ke vector store yang berisi dokumen dan embedding.
        
        PARAMS / PARAMETER:
        - vector_store: VectorStore instance containing documents and their embeddings / Instance VectorStore yang berisi dokumen dan embedding mereka
        """
        self.vector_store = vector_store

    def search(self, query: str, top_k: int = 1, lexical_weight: float = 0.2) -> list[RetrievalResult]:
        """
        Search for documents most relevant to the query using hybrid approach.
        
        PURPOSE / TUJUAN:
        - EN: Performs hybrid search combining semantic similarity and lexical matching, returning top-k most relevant documents.
        - ID: Melakukan pencarian hibrida yang menggabungkan kesamaan semantik dan pencocokan leksikal, mengembalikan k dokumen paling relevan.
        
        PARAMS / PARAMETER:
        - query (str): The search query text / Teks kueri pencarian
        - top_k (int): Number of top results to return (default: 1) / Jumlah hasil teratas yang akan dikembalikan (default: 1)
        - lexical_weight (float): Weight for lexical score (0.0-1.0), semantic weight = 1 - lexical_weight / Bobot untuk skor leksikal (0.0-1.0), bobot semantik = 1 - bobot_leksikal
        
        RETURNS / HASIL:
        - list[RetrievalResult]: List of top-k results sorted by combined score, highest first / Daftar hasil k teratas diurutkan berdasarkan skor gabungan, tertinggi terlebih dahulu
        
        RAISES / MELEMPAR:
        - ValueError: If top_k <= 0 or lexical_weight not in [0, 1] / Jika top_k <= 0 atau lexical_weight bukan dalam [0, 1]
        
        HOW IT WORKS / CARA KERJANYA:
        1. Embed the query using EmbeddingService / Embed kueri menggunakan EmbeddingService
        2. Calculate semantic score for each document / Hitung skor semantik untuk setiap dokumen
        3. Calculate lexical score based on keyword matching / Hitung skor leksikal berdasarkan pencocokan kata kunci
        4. Combine scores: combined = (1 - lexical_weight) * semantic + lexical_weight * lexical / Gabungkan skor: gabungan = (1 - lexical_weight) * semantic + lexical_weight * lexical
        5. Return top-k results / Kembalikan hasil k teratas
        """
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
    """
    Tokenize text into meaningful tokens, filtering stopwords.
    
    PURPOSE / TUJUAN:
    - EN: Splits text into individual tokens (words), removes stopwords, and keeps only tokens with 2+ characters.
    - ID: Membagi teks menjadi token individual (kata), menghapus stopwords, dan hanya menyimpan token dengan 2+ karakter.
    
    PARAMS / PARAMETER:
    - text (str): Normalized text to tokenize / Teks yang dinormalisasi untuk di-tokenisasi
    
    RETURNS / HASIL:
    - set[str]: Set of cleaned tokens (stopwords removed) / Set token yang dibersihkan (stopwords dihapus)
    """
    return {
        token
        for token in re.split(r"[^a-zA-Z0-9]+", text.lower())
        if len(token) >= 2 and token not in STOPWORDS
    }


def _normalize_text(text: str) -> str:
    """
    Normalize text by converting to lowercase and collapsing whitespace.
    
    PURPOSE / TUJUAN:
    - EN: Standardizes text by lowercasing and removing extra whitespace for consistent processing.
    - ID: Menstandarkan teks dengan mengubah ke huruf kecil dan menghapus whitespace ekstra untuk pemrosesan yang konsisten.
    
    PARAMS / PARAMETER:
    - text (str): Raw text to normalize / Teks mentah untuk dinormalisasi
    
    RETURNS / HASIL:
    - str: Normalized text (lowercase, single spaces, trimmed) / Teks yang dinormalisasi (huruf kecil, spasi tunggal, dipotong)
    """
    return re.sub(r"\s+", " ", text.lower()).strip()


def _lexical_score(query_tokens: set[str], normalized_query: str, document: str) -> float:
    """
    Calculate lexical relevance score based on keyword matching and phrase matching.
    
    PURPOSE / TUJUAN:
    - EN: Measures how well the document matches the query based on shared keywords and phrase presence.
    - ID: Mengukur seberapa baik dokumen cocok dengan kueri berdasarkan kata kunci bersama dan kehadiran frasa.
    
    PARAMS / PARAMETER:
    - query_tokens (set[str]): Set of query tokens (keywords) / Set token kueri (kata kunci)
    - normalized_query (str): Normalized full query text / Teks kueri penuh yang dinormalisasi
    - document (str): Full document text to score / Teks dokumen penuh untuk di-score
    
    RETURNS / HASIL:
    - float: Lexical score in range [0.0, 1.0] / Skor leksikal dalam kisaran [0.0, 1.0]
    
    SCORING LOGIC / LOGIKA SCORING:
    - Base score: token_coverage = intersection_tokens / total_query_tokens / Skor dasar: coverage_token = token_intersection / total_query_tokens
    - Bonus: +0.2 if query phrase (16+ chars) is found verbatim in document / Bonus: +0.2 jika frasa kueri (16+ karakter) ditemukan verbatim dalam dokumen
    - Final score: min(1.0, coverage + bonus) / Skor akhir: min(1.0, coverage + bonus)
    """
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
    """
    Extract metadata value from document header by key.
    
    PURPOSE / TUJUAN:
    - EN: Parses the document's metadata section (first 8 lines) to extract specific key-value pairs.
    - ID: Mem-parse bagian metadata dokumen (8 baris pertama) untuk mengekstrak pasangan kunci-nilai tertentu.
    
    PARAMS / PARAMETER:
    - document (str): Full document text / Teks dokumen lengkap
    - key (str): Metadata key to look for (e.g., "Sumber", "Judul") / Kunci metadata yang dicari (mis. "Sumber", "Judul")
    
    RETURNS / HASIL:
    - str: Metadata value for the key, or empty string if not found / Nilai metadata untuk kunci, atau string kosong jika tidak ditemukan
    
    METADATA FORMAT / FORMAT METADATA:
    Each metadata line should follow: "Key: Value" / Setiap baris metadata harus mengikuti: "Kunci: Nilai"
    Example / Contoh:
    Sumber: https://example.com
    Judul: Article Title
    """
    prefix = f"{key}:"
    for line in document.splitlines()[:8]:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return ""
