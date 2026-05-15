"""
Flask Web Application for RAG Chatbot.

PURPOSE / TUJUAN:
- EN: Provides a web interface for interacting with the RAG system through HTTP endpoints.
- ID: Menyediakan antarmuka web untuk berinteraksi dengan sistem RAG melalui endpoint HTTP.

FEATURES / FITUR:
- Chat interface dengan streaming responses / Antarmuka chat dengan respons streaming
- Configuration management / Manajemen konfigurasi
- Real-time document retrieval visualization / Visualisasi retrieval dokumen real-time
- Responsive design dengan Tailwind CSS / Desain responsif dengan Tailwind CSS
"""

import sys
from pathlib import Path

from flask import (
    Flask,
    Response,
    render_template,
    request,
    jsonify,
)
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

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
from main import (
    load_documents,
    build_context,
    build_news_context,
    _is_news_query,
)

# Initialize Flask app
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)
CORS(app)

# Global variables
documents = None
vector_store = None
retriever = None


def initialize_rag_system() -> None:
    """
    Initialize RAG system components.

    PURPOSE / TUJUAN:
    - EN: Loads documents, builds vector store, and creates retriever for RAG system.
    - ID: Memuat dokumen, membangun vector store, dan membuat retriever untuk sistem RAG.
    """
    global documents, vector_store, retriever

    print("[web] Initializing RAG system...")
    documents = load_documents()
    print(f"[web] Loaded {len(documents)} documents")

    vector_store = VectorStore(documents=documents)
    print("[web] Built vector store with embeddings")

    retriever = Retriever(vector_store)
    print("[web] Created retriever")


@app.route("/", methods=["GET"])
def index() -> str:
    """
    Render main chat interface.

    PURPOSE / TUJUAN:
    - EN: Renders the main chat page with responsive UI design.
    - ID: Merender halaman chat utama dengan desain UI responsif.
    """
    return render_template("chat.html")


@app.route("/api/chat", methods=["POST"])
def chat_api() -> Response:
    """
    API endpoint for chat queries.

    PURPOSE / TUJUAN:
    - EN: Processes user query and returns AI-generated response with retrieved context.
    - ID: Memproses kueri pengguna dan mengembalikan respons yang dihasilkan AI dengan konteks yang diambil.

    REQUEST / PERMINTAAN:
    - query (str): User question / Pertanyaan pengguna
    - show_context (bool): Whether to include retrieved context in response / Apakah akan menyertakan konteks yang diambil

    RETURNS / HASIL:
    - JSON response with answer, context, and metadata / Respons JSON dengan jawaban, konteks, dan metadata
    """
    data = request.json
    query = data.get("query", "").strip()
    show_context = data.get("show_context", False)

    if not query:
        return jsonify({"error": "Query tidak boleh kosong"}, 400)

    if not retriever:
        return jsonify({"error": "RAG system belum siap"}, 503)

    try:
        # Retrieve documents
        candidate_k = RETRIEVER_TOP_K * RETRIEVER_CANDIDATE_MULTIPLIER
        results = retriever.search(
            query=query,
            top_k=candidate_k,
            lexical_weight=RETRIEVER_LEXICAL_WEIGHT,
        )

        if not results:
            return jsonify(
                {
                    "answer": "Dokumen tidak tersedia untuk dijadikan konteks.",
                    "context": "",
                    "context_count": 0,
                    "is_news": False,
                }
            )

        # Build context
        is_news = _is_news_query(query)
        if is_news:
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

        # Generate answer
        answer = ChatService.generate(context=context, query=query)

        return jsonify(
            {
                "answer": answer,
                "context": context if show_context else "",
                "context_count": len(results),
                "is_news": is_news,
                "retrieval_results": [
                    {
                        "document": (
                            r.document[:200] + "..."
                            if len(r.document) > 200
                            else r.document
                        ),
                        "score": round(r.score, 3),
                        "semantic_score": round(r.semantic_score, 3),
                        "lexical_score": round(r.lexical_score, 3),
                        "source_url": r.source_url,
                        "title": r.title,
                    }
                    for r in results[:5]
                ],
            }
        )

    except Exception as e:
        return jsonify({"error": f"Error processing query: {str(e)}"}, 500)


@app.route("/api/config", methods=["GET"])
def get_config() -> Response:
    """
    Get current RAG system configuration.

    PURPOSE / TUJUAN:
    - EN: Returns all current configuration settings for display in UI.
    - ID: Mengembalikan semua pengaturan konfigurasi saat ini untuk ditampilkan di UI.
    """
    return jsonify(
        {
            "base_url": OPENROUTER_BASE_URL,
            "embedding_model": EMBEDDING_MODEL,
            "chat_model": CHAT_MODEL,
            "scrape_urls": SCRAPE_URLS,
            "scrape_follow_links": SCRAPE_FOLLOW_LINKS,
            "scrape_max_links_per_url": SCRAPE_MAX_LINKS_PER_URL,
            "scrape_max_total_urls": SCRAPE_MAX_TOTAL_URLS,
            "scrape_timeout_seconds": SCRAPE_TIMEOUT_SECONDS,
            "scrape_chunk_size": SCRAPE_CHUNK_SIZE,
            "scrape_chunk_overlap": SCRAPE_CHUNK_OVERLAP,
            "scrape_min_text_length": SCRAPE_MIN_TEXT_LENGTH,
            "retriever_top_k": RETRIEVER_TOP_K,
            "retriever_candidate_multiplier": RETRIEVER_CANDIDATE_MULTIPLIER,
            "retriever_lexical_weight": RETRIEVER_LEXICAL_WEIGHT,
            "retriever_max_per_source": RETRIEVER_MAX_PER_SOURCE,
            "max_context_chars": MAX_CONTEXT_CHARS,
            "news_max_stories": NEWS_MAX_STORIES,
            "show_retrieved_context": SHOW_RETRIEVED_CONTEXT,
        }
    )


@app.route("/api/health", methods=["GET"])
def health_check() -> Response:
    """
    Health check endpoint.

    PURPOSE / TUJUAN:
    - EN: Simple endpoint to verify API is running and RAG system is initialized.
    - ID: Endpoint sederhana untuk memverifikasi API berjalan dan sistem RAG diinisialisasi.
    """
    is_ready = retriever is not None
    return jsonify(
        {
            "status": "ready" if is_ready else "initializing",
            "documents_loaded": len(documents) if documents else 0,
            "system_ready": is_ready,
        }
    )


@app.route("/api/documents/count", methods=["GET"])
def get_documents_count() -> Response:
    """
    Get count of loaded documents.

    PURPOSE / TUJUAN:
    - EN: Returns the number of documents currently loaded in the vector store.
    - ID: Mengembalikan jumlah dokumen yang saat ini dimuat di vector store.
    """
    return jsonify(
        {
            "count": len(documents) if documents else 0,
        }
    )


@app.route("/api/examples", methods=["GET"])
def get_examples() -> Response:
    """
    Get example queries for the user.

    PURPOSE / TUJUAN:
    - EN: Returns list of example queries to help users understand the system.
    - ID: Mengembalikan daftar contoh kueri untuk membantu pengguna memahami sistem.
    """
    examples = [
        "Apa itu machine learning?",
        "Bagaimana cara menggunakan Python?",
        "Apa berita terbaru hari ini?",
        "Jelaskan tentang artificial intelligence",
        "Apa itu docker dan kubernetes?",
        "Bagaimana cara menggunakan git?",
    ]
    return jsonify({"examples": examples})


@app.errorhandler(404)
def not_found(error) -> tuple:
    """Handle 404 errors."""
    return jsonify({"error": f"Endpoint not found {error}"}), 404


@app.errorhandler(500)
def server_error(error) -> tuple:
    """Handle 500 errors."""
    return jsonify({"error": f"Internal server error {error}"}), 500


if __name__ == "__main__":
    try:
        initialize_rag_system()
        print("[web] Starting Flask development server...")
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        print(f"[web] Error starting server: {e}")
        sys.exit(1)
