import re

from config import (
    CHAT_MODEL,
    EMBEDDING_MODEL,
    MAX_CONTEXT_CHARS,
    NEWS_MAX_STORIES,
    OPENROUTER_BASE_URL,
    RETRIEVER_CANDIDATE_MULTIPLIER,
    RETRIEVER_LEXICAL_WEIGHT,
    RETRIEVER_MAX_PER_SOURCE,
    RETRIEVER_TOP_K,
    SCRAPE_CHUNK_OVERLAP,
    SCRAPE_CHUNK_SIZE,
    SCRAPE_FOLLOW_LINKS,
    SCRAPE_MAX_LINKS_PER_URL,
    SCRAPE_MAX_TOTAL_URLS,
    SCRAPE_MIN_TEXT_LENGTH,
    SCRAPE_TIMEOUT_SECONDS,
    SCRAPE_URLS,
    SHOW_RETRIEVED_CONTEXT,
)
from core.retriever import RetrievalResult, Retriever
from core.vector_store import VectorStore
from data.documents import documents as fallback_documents
from service.chat_service import ChatService
from service.scraper_service import ScraperService


NEWS_QUERY_HINTS = {
    "news",
    "latest",
    "today",
    "headline",
    "headlines",
    "berita",
    "terbaru",
    "update",
}

NEWS_SOURCE_HINTS = {
    "news",
    "headline",
    "latest",
    "update",
    "breaking",
}


def load_documents() -> list[str]:
    """
    Load documents from web scraping or use fallback built-in documents.
    
    PURPOSE / TUJUAN:
    - EN: Loads documents from configured URLs using web scraper, or falls back to built-in sample documents if no URLs configured.
    - ID: Memuat dokumen dari URL yang dikonfigurasi menggunakan web scraper, atau kembali ke dokumen sampel bawaan jika tidak ada URL yang dikonfigurasi.
    
    RETURNS / HASIL:
    - list[str]: List of documents ready for embedding and retrieval / Daftar dokumen siap untuk embedding dan retrieval
    
    PROCESS / PROSES:
    1. Check if SCRAPE_URLS is configured / Periksa apakah SCRAPE_URLS dikonfigurasi
    2. If empty, return fallback documents / Jika kosong, kembalikan dokumen fallback
    3. If configured, scrape URLs with expansion and link following / Jika dikonfigurasi, scrape URL dengan ekspansi dan pengikutan tautan
    4. Convert scraped pages to chunked documents / Konversi halaman yang di-scrape ke dokumen chunked
    5. Return scraped documents if successful, otherwise fallback / Kembalikan dokumen yang di-scrape jika berhasil, jika tidak kembali fallback
    
    LOGGING / PENCATATAN:
    - Prints progress: number of pages, chunks, etc. / Mencetak kemajuan: jumlah halaman, chunk, dll.
    - Prints fallback message if scraping fails / Mencetak pesan fallback jika scraping gagal
    """
    if not SCRAPE_URLS:
        print("[scraper] SCRAPE_URLS kosong, pakai dokumen bawaan")
        return fallback_documents

    print(f"[scraper] mulai scrape {len(SCRAPE_URLS)} URL")
    pages = ScraperService.scrape_expanded(
        urls=SCRAPE_URLS,
        timeout_seconds=SCRAPE_TIMEOUT_SECONDS,
        min_text_length=SCRAPE_MIN_TEXT_LENGTH,
        follow_links=SCRAPE_FOLLOW_LINKS,
        max_links_per_url=SCRAPE_MAX_LINKS_PER_URL,
        max_total_urls=SCRAPE_MAX_TOTAL_URLS,
    )

    scraped_documents = ScraperService.to_documents(
        pages=pages,
        chunk_size=SCRAPE_CHUNK_SIZE,
        chunk_overlap=SCRAPE_CHUNK_OVERLAP,
    )

    if scraped_documents:
        print(
            f"[scraper] selesai: {len(pages)} halaman, "
            f"{len(scraped_documents)} chunk dokumen"
        )
        return scraped_documents

    print("[scraper] gagal dapat dokumen valid, fallback ke dokumen bawaan")
    return fallback_documents


def build_context(results: list[RetrievalResult], max_per_source: int, max_chars: int) -> str:
    """
    Build formatted context string from retrieval results for non-news queries.
    
    PURPOSE / TUJUAN:
    - EN: Formats search results into a structured context string, limiting results per source and total characters.
    - ID: Memformat hasil pencarian menjadi string konteks terstruktur, membatasi hasil per sumber dan total karakter.
    
    PARAMS / PARAMETER:
    - results (list[RetrievalResult]): Retrieved documents with scores / Dokumen yang diambil dengan skor
    - max_per_source (int): Maximum results per unique source URL / Hasil maksimal per URL sumber unik
    - max_chars (int): Maximum total character length of context / Panjang karakter total maksimal konteks
    
    RETURNS / HASIL:
    - str: Formatted context with score information / Konteks yang diformat dengan informasi skor
    
    FORMAT / FORMAT:
    [Konteks 1]
    Skor: 0.95 (semantic=0.96, lexical=0.92)
    {document text}
    
    [Konteks 2]
    ...
    
    SELECTION LOGIC / LOGIKA SELEKSI:
    1. Rank results (published date, news source, lexical score, semantic score) / Urutkan hasil
    2. Select results respecting max_per_source limit / Pilih hasil dengan menghormati batas max_per_source
    3. Add to context while respecting max_chars limit / Tambahkan ke konteks sambil menghormati batas max_chars
    4. Stop if adding next result would exceed max_chars / Berhenti jika menambahkan hasil berikutnya akan melebihi max_chars
    """
    selected: list[RetrievalResult] = []
    source_counts: dict[str, int] = {}

    for result in _rank_results_for_context(results):
        source_key = result.source_url or "unknown"
        current_count = source_counts.get(source_key, 0)
        if current_count >= max_per_source:
            continue

        source_counts[source_key] = current_count + 1
        selected.append(result)

    sections: list[str] = []
    current_chars = 0
    for index, result in enumerate(selected, start=1):
        section = "\n".join(
            [
                f"[Konteks {index}]",
                f"Skor: {result.score:.3f} (semantic={result.semantic_score:.3f}, lexical={result.lexical_score:.3f})",
                result.document,
            ]
        )

        projected = current_chars + len(section) + (2 if sections else 0)
        if projected > max_chars and sections:
            break

        sections.append(section)
        current_chars = projected

    return "\n\n".join(sections)


def build_news_context(results: list[RetrievalResult], max_stories: int, max_chars: int) -> str:
    """
    Build formatted context string from retrieval results optimized for news queries.
    
    PURPOSE / TUJUAN:
    - EN: Formats news articles into stories, deduplicating by source and headline, prioritizing newer/better content.
    - ID: Memformat artikel berita menjadi cerita, mendeduplikasi berdasarkan sumber dan headline, memprioritaskan konten yang lebih baru/lebih baik.
    
    PARAMS / PARAMETER:
    - results (list[RetrievalResult]): Retrieved documents / Dokumen yang diambil
    - max_stories (int): Maximum number of distinct news stories to include / Jumlah maksimal cerita berita yang berbeda untuk disertakan
    - max_chars (int): Maximum total character length of context / Panjang karakter total maksimal konteks
    
    RETURNS / HASIL:
    - str: Formatted news context, or falls back to regular context if no news stories found / Konteks berita yang diformat, atau kembali ke konteks reguler jika tidak ada cerita berita ditemukan
    
    NEWS STORY IDENTIFICATION / IDENTIFIKASI CERITA BERITA:
    - Checks if content looks like a news story (title length, source type, URL structure) / Memeriksa apakah konten terlihat seperti cerita berita
    - Groups by story key (URL or title) / Mengelompokkan berdasarkan kunci cerita (URL atau judul)
    - Keeps best-scoring version of each story / Menyimpan versi dengan skor terbaik dari setiap cerita
    
    RANKING FACTORS / FAKTOR PERINGKAT:
    1. Has published date (more recent news first) / Memiliki tanggal publikasi (berita lebih baru terlebih dahulu)
    2. Lexical score (keyword match) / Skor leksikal (pencocokan kata kunci)
    3. Semantic score (relevance) / Skor semantik (relevansi)
    """
    story_best: dict[str, RetrievalResult] = {}

    for result in results:
        if not _looks_like_news_story(result):
            continue

        key = _story_key(result)
        current = story_best.get(key)
        if current is None or result.score > current.score:
            story_best[key] = result

    ranked = sorted(story_best.values(), key=_news_rank_key, reverse=True)
    selected = ranked[:max_stories]

    sections: list[str] = []
    current_chars = 0
    for index, result in enumerate(selected, start=1):
        section = "\n".join(
            [
                f"[Berita {index}]",
                f"Skor: {result.score:.3f} (semantic={result.semantic_score:.3f}, lexical={result.lexical_score:.3f})",
                result.document,
            ]
        )

        projected = current_chars + len(section) + (2 if sections else 0)
        if projected > max_chars and sections:
            break

        sections.append(section)
        current_chars = projected

    if sections:
        return "\n\n".join(sections)

    return build_context(results=results, max_per_source=RETRIEVER_MAX_PER_SOURCE, max_chars=max_chars)


def _rank_results_for_context(results: list[RetrievalResult]) -> list[RetrievalResult]:
    return sorted(
        results,
        key=lambda item: (
            _has_published_date(item.document),
            _looks_like_news_source(item.source_url, item.title),
            item.lexical_score,
            item.score,
        ),
        reverse=True,
    )


def _has_published_date(document: str) -> bool:
    for line in document.splitlines()[:8]:
        if line.startswith("Terbit:"):
            value = line[len("Terbit:") :].strip().lower()
            return value not in {"", "none", "null"}
    return False


def _is_news_query(query: str) -> bool:
    """
    Detect if query is asking for news or recent information.
    
    PURPOSE / TUJUAN:
    - EN: Analyzes query text to determine if user is asking for news, breaking news, latest updates, or current events.
    - ID: Menganalisis teks kueri untuk menentukan apakah pengguna menanyakan berita, berita terakhir, pembaruan terbaru, atau acara terkini.
    
    PARAMS / PARAMETER:
    - query (str): User query string / String kueri pengguna
    
    RETURNS / HASIL:
    - bool: True if query appears to be news-related, False otherwise / True jika kueri tampaknya terkait berita, False sebaliknya
    
    DETECTION METHODS / METODE DETEKSI:
    1. Check for news-related keywords / Periksa kata kunci terkait berita
       - English: "news", "latest", "today", "headline", "headlines", "breaking", "what happened"
       - Indonesian: "berita", "terbaru", "hari ini", "update"
    2. Check for news phrases / Periksa frasa berita
       - "hari ini" (today)
       - "berita terbaru" (latest news)
    
    EXAMPLE / CONTOH:
    _is_news_query("Apa berita terbaru?")  # True
    _is_news_query("Berapa suhu matahari?")  # False
    """
    lowered = query.lower()
    tokens = [token for token in lowered.replace("?", " ").split() if token]
    if any(token in NEWS_QUERY_HINTS for token in tokens):
        return True

    if "hari ini" in lowered or "berita terbaru" in lowered:
        return True

    return "breaking" in lowered or "what happened" in lowered


def _looks_like_news_source(url: str, title: str) -> bool:
    target = f"{url} {title}".lower()
    return any(keyword in target for keyword in NEWS_SOURCE_HINTS)


def _looks_like_news_story(result: RetrievalResult) -> bool:
    url = result.source_url.lower()
    title = result.title.strip().lower()
    parsed_path = re.sub(r"/+$", "", re.sub(r"https?://[^/]+", "", url)) or "/"

    if not title or len(title) < 20:
        return False
    if not _looks_like_news_source(result.source_url, result.title):
        return False

    if parsed_path in {"/", "/news"}:
        return False

    if any(token in title for token in ["live updates", "live blog", "live:", "breaking"]):
        return True

    if url.endswith("/news") or url.endswith("/news/"):
        return False
    if "/news/articles/" in url:
        return True
    if re.search(r"/20\d{2}/\d{2}/\d{2}/", url):
        return True
    if any(token in url for token in ["/news/", "/world/", "/politics/", "/business/", "/technology/"]):
        return True

    return False


def _story_key(result: RetrievalResult) -> str:
    return result.source_url or result.title


def _news_rank_key(result: RetrievalResult) -> tuple[bool, float, float]:
    return (
        _has_published_date(result.document),
        result.lexical_score,
        result.score,
    )


def main() -> None:
    """
    Main entry point for the RAG chatbot application.
    
    PURPOSE / TUJUAN:
    - EN: Initializes RAG system (loads documents, builds vector store, creates retriever) and runs interactive chat loop.
    - ID: Menginisialisasi sistem RAG (memuat dokumen, membangun vector store, membuat retriever) dan menjalankan loop obrolan interaktif.
    
    WORKFLOW / ALUR KERJA:
    1. Print configuration for debugging / Cetak konfigurasi untuk debugging
    2. Load documents (from web or fallback) / Muat dokumen (dari web atau fallback)
    3. Build vector store with embeddings / Bangun vector store dengan embedding
    4. Create retriever with vector store / Buat retriever dengan vector store
    5. Enter interactive loop / Masuk loop interaktif
    
    INTERACTIVE LOOP / LOOP INTERAKTIF:
    - Read user query from stdin / Baca kueri pengguna dari stdin
    - Exit if user types "exit" or "quit" / Keluar jika pengguna mengetik "exit" atau "quit"
    - Retrieve relevant documents using hybrid search / Ambil dokumen relevan menggunakan pencarian hibrida
    - Detect if query is news-related / Deteksi apakah kueri terkait berita
    - Build context (regular or news-specific) / Bangun konteks (reguler atau spesifik berita)
    - Generate answer using LLM with context / Hasilkan jawaban menggunakan LLM dengan konteks
    - Display answer (optionally show retrieved context) / Tampilkan jawaban (secara opsional tunjukkan konteks yang diambil)
    
    CONFIGURATION / KONFIGURASI:
    - Prints all settings at startup for transparency / Mencetak semua pengaturan saat startup untuk transparansi
    - See config.py for all available settings / Lihat config.py untuk semua pengaturan yang tersedia
    
    USER INTERFACE / ANTARMUKA PENGGUNA:
    - Prompt: ">> " / Prompt: ">> "
    - Output: "answer: {response}" / Output: "answer: {response}"
    - Exit message: "bye" / Pesan keluar: "bye"
    """
    print("[config] base_url:", OPENROUTER_BASE_URL)
    print("[config] embedding_model:", EMBEDDING_MODEL)
    print("[config] chat_model:", CHAT_MODEL)
    print("[config] scrape_urls:", SCRAPE_URLS)
    print("[config] scrape_follow_links:", SCRAPE_FOLLOW_LINKS)
    print("[config] scrape_max_links_per_url:", SCRAPE_MAX_LINKS_PER_URL)
    print("[config] scrape_max_total_urls:", SCRAPE_MAX_TOTAL_URLS)
    print("[config] retriever_top_k:", RETRIEVER_TOP_K)
    print("[config] retriever_candidate_multiplier:", RETRIEVER_CANDIDATE_MULTIPLIER)
    print("[config] retriever_lexical_weight:", RETRIEVER_LEXICAL_WEIGHT)
    print("[config] retriever_max_per_source:", RETRIEVER_MAX_PER_SOURCE)
    print("[config] max_context_chars:", MAX_CONTEXT_CHARS)
    print("[config] news_max_stories:", NEWS_MAX_STORIES)
    print("[config] show_retrieved_context:", SHOW_RETRIEVED_CONTEXT)

    documents = load_documents()
    vector_store = VectorStore(documents=documents)
    retriever = Retriever(vector_store)

    while True:
        query = input(">> ").strip()
        if not query:
            continue

        if query.lower() in {"exit", "quit"}:
            print("bye")
            break

        candidate_k = RETRIEVER_TOP_K * RETRIEVER_CANDIDATE_MULTIPLIER
        results = retriever.search(
            query=query,
            top_k=candidate_k,
            lexical_weight=RETRIEVER_LEXICAL_WEIGHT,
        )
        if not results:
            print("\n answer: Dokumen tidak tersedia untuk dijadikan konteks.\n")
            continue

        if _is_news_query(query):
            context = build_news_context(
                results=results,
                max_stories=NEWS_MAX_STORIES,
                max_chars=MAX_CONTEXT_CHARS,
            )
            context = (
                "[Instruksi tambahan]\n"
                "Prioritaskan item dengan metadata 'Terbit' terbaru jika tersedia.\n"
                "Jika hanya ada headline, jelaskan keterbatasannya secara eksplisit.\n\n"
                f"{context}"
            )
        else:
            context = build_context(
                results=results,
                max_per_source=RETRIEVER_MAX_PER_SOURCE,
                max_chars=MAX_CONTEXT_CHARS,
            )

        answer = ChatService.generate(context=context, query=query)

        if SHOW_RETRIEVED_CONTEXT:
            print(f"\n context:\n{context}")

        print(f" answer: {answer}\n")


if __name__ == "__main__":
    main()
