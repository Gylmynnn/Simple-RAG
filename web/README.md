# RAG Chatbot Web Interface

Web UI yang indah dan responsif untuk sistem RAG Chatbot, dibangun dengan Flask dan Tailwind CSS.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Configure Environment

Buat file `.env` di root directory dengan konfigurasi API Anda:

```bash
OPENROUTER_API_KEY=your_api_key_here
CHAT_MODEL=google/gemini-2.5-flash-preview:free
EMBEDDING_MODEL=openai/text-embedding-3-small
```

### 3. Run Web Server

```bash
# Development server (debug mode on localhost:5000)
python run_web.py

# Custom host and port
python run_web.py --host 0.0.0.0 --port 8000

# Production mode
python run_web.py --no-debug
```

### 4. Open Browser

Buka browser dan akses:
- **Main Chat**: `http://localhost:5000/`
- **Configuration**: `http://localhost:5000/config`

---

## 📁 Project Structure

```
web/
├── __init__.py                 # Web module initialization
├── app.py                      # Flask application & API endpoints
├── templates/
│   ├── base.html              # Base template dengan Tailwind CSS
│   ├── chat.html              # Chat interface utama
│   └── config.html            # Configuration page
├── static/
│   ├── css/
│   │   └── style.css          # Custom CSS styles
│   └── js/
│       └── (JavaScript inline di templates)
└── README.md                   # Documentation ini
```

---

## 🎨 Features

### Chat Interface
- ✨ **Real-time Chat**: Interface chat yang responsif dan user-friendly
- 🔍 **Document Retrieval**: Visualisasi dokumen yang di-retrieve
- 📝 **Context Display**: Lihat konteks penuh dari retrieval results
- 🎯 **Smart Suggestions**: Contoh pertanyaan untuk memandu user

### Configuration Page
- ⚙️ **System Configuration**: Lihat semua settings RAG system
- 📊 **System Statistics**: Jumlah dokumen, status sistem
- 🔧 **Detailed Parameters**: Konfigurasi scraper, retriever, API

### Design
- 🎨 **Tailwind CSS**: Modern, responsive design
- 📱 **Mobile Friendly**: Responsif di semua ukuran layar
- 🌓 **Smooth Animations**: Transisi dan animasi yang halus
- ♿ **Accessible**: WCAG compliant interface

---

## 📡 API Endpoints

### Chat API
```
POST /api/chat

Request:
{
    "query": "Apa itu AI?",
    "show_context": false
}

Response:
{
    "answer": "AI adalah kecerdasan buatan...",
    "context": "...",
    "context_count": 5,
    "is_news": false,
    "retrieval_results": [...]
}
```

### Configuration API
```
GET /api/config

Response:
{
    "base_url": "https://openrouter.ai/api/v1",
    "chat_model": "google/gemini-2.5-flash-preview:free",
    "embedding_model": "openai/text-embedding-3-small",
    "scrape_urls": [...],
    ...
}
```

### Health Check API
```
GET /api/health

Response:
{
    "status": "ready",
    "documents_loaded": 45,
    "system_ready": true
}
```

### Examples API
```
GET /api/examples

Response:
{
    "examples": [
        "Apa itu machine learning?",
        "Bagaimana cara menggunakan Python?",
        ...
    ]
}
```

---

## 🔧 Configuration

### Environment Variables

Semua konfigurasi diatur melalui `.env` file dan dapat dilihat di halaman Konfigurasi:

**API Configuration**
- `OPENROUTER_BASE_URL`: Base URL untuk OpenRouter API
- `OPENROUTER_API_KEY` atau `OPENAI_API_KEY`: API key untuk authentication
- `CHAT_MODEL`: Model LLM untuk chat
- `EMBEDDING_MODEL`: Model untuk text embeddings

**Scraper Configuration**
- `SCRAPE_URLS`: Comma-separated list of URLs to scrape
- `SCRAPE_FOLLOW_LINKS`: Follow links dalam scraping (true/false)
- `SCRAPE_TIMEOUT_SECONDS`: Timeout untuk HTTP requests
- `SCRAPE_CHUNK_SIZE`: Ukuran chunk untuk text splitting
- `SCRAPE_CHUNK_OVERLAP`: Overlap antara chunks
- `SCRAPE_MIN_TEXT_LENGTH`: Minimum text length untuk disimpan
- `SCRAPE_MAX_LINKS_PER_URL`: Max links per URL
- `SCRAPE_MAX_TOTAL_URLS`: Max total URLs

**Retriever Configuration**
- `RETRIEVER_TOP_K`: Number of documents to retrieve
- `RETRIEVER_CANDIDATE_MULTIPLIER`: Multiplier untuk candidate selection
- `RETRIEVER_LEXICAL_WEIGHT`: Weight untuk lexical search (0-1)
- `RETRIEVER_MAX_PER_SOURCE`: Max results per source URL
- `MAX_CONTEXT_CHARS`: Maximum character length untuk context
- `NEWS_MAX_STORIES`: Max stories untuk news queries
- `SHOW_RETRIEVED_CONTEXT`: Show context di response

---

## 💡 Usage Examples

### Basic Chat Query
```javascript
const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        query: "Apa itu machine learning?",
        show_context: false
    })
});
const data = await response.json();
console.log(data.answer);
```

### Get Configuration
```javascript
const config = await fetch('/api/config').then(r => r.json());
console.log(`Chat Model: ${config.chat_model}`);
console.log(`Embedding Model: ${config.embedding_model}`);
```

---

## 🎯 Hybrid Search System

Web interface memanfaatkan **Hybrid Search** yang menggabungkan:

1. **Semantic Search**: 
   - Menggunakan embedding vectors
   - Mencari kesamaan makna
   - Weight: `1 - RETRIEVER_LEXICAL_WEIGHT`

2. **Lexical Search**:
   - Menggunakan keyword matching
   - Mencari term frequency
   - Weight: `RETRIEVER_LEXICAL_WEIGHT`

**Scoring Formula**:
```
combined_score = (1 - lexical_weight) * semantic_score + lexical_weight * lexical_score
```

---

## 📊 Performance Tips

### Optimization
1. **Reduce Document Count**: Fewer documents = faster retrieval
2. **Adjust TOP_K**: Lower TOP_K untuk response lebih cepat
3. **Tune LEXICAL_WEIGHT**: Lexical search lebih cepat dari semantic
4. **Use Threading**: Run dengan `--threaded` untuk concurrent requests

### Monitoring
- Check `/api/health` untuk system status
- Monitor document count di config page
- Track message count untuk usage analytics

---

## 🐛 Troubleshooting

### Issue: "RAG system belum siap"
**Solution**: Tunggu beberapa detik untuk inisialisasi. Check logs untuk errors.

### Issue: API Key not found
**Solution**: Pastikan `OPENROUTER_API_KEY` atau `OPENAI_API_KEY` di-set di `.env`

### Issue: No documents loaded
**Solution**: 
- Jika `SCRAPE_URLS` kosong, sistem akan gunakan fallback documents
- Check logs untuk scraping errors
- Verify `SCRAPE_URLS` configuration

### Issue: Slow responses
**Solution**:
- Reduce `RETRIEVER_CANDIDATE_MULTIPLIER`
- Lower `SCRAPE_CHUNK_SIZE` untuk faster processing
- Increase `RETRIEVER_LEXICAL_WEIGHT` (lexical search lebih cepat)

---

## 🚀 Deployment

### Production Setup

```bash
# Install production dependencies
pip install -r requirements.txt gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "web.app:app"
```

### Docker Support (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
CMD ["python", "run_web.py", "--host", "0.0.0.0", "--port", "5000"]
```

---

## 📚 Technologies

- **Backend**: Flask 2.3+
- **Frontend**: HTML5, TailwindCSS, Alpine.js
- **AI/ML**: OpenAI API, LangChain concepts
- **Database**: In-memory vector store
- **Icons**: Font Awesome 6.4

---

## 📝 License

Same as main RAG Chatbot project

---

## 🤝 Contributing

Contributions welcome! Please follow the coding style and documentation format dari main project.

---

## 📞 Support

Untuk issues atau questions:
1. Check dokumentasi
2. Review logs
3. Check API responses dengan browser DevTools
4. Create issue di GitHub

---

**Created**: 2024  
**Version**: 1.0.0  
**Status**: Production Ready
