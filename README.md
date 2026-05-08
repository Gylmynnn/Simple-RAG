# Simple RAG CLI

Project ini sekarang mendukung dokumen dari scraping web (BeautifulSoup), bukan hardcode saja.

## Setup

1. Install dependency:

```bash
uv sync
```

2. Buat file env:

```bash
cp .env.example .env
```

3. Isi minimal nilai ini di `.env`:

- `OPENROUTER_API_KEY`: API key OpenRouter
- `SCRAPE_URLS`: daftar URL dipisahkan koma

## Menjalankan aplikasi

```bash
uv run python main.py
```

Di prompt `>>`, ketik pertanyaan. Ketik `exit` atau `quit` untuk keluar.

## Penjelasan command/config penting

- `SCRAPE_URLS`: URL sumber dokumen, contoh `https://en.wikipedia.org/wiki/Artificial_intelligence`
- `SCRAPE_TIMEOUT_SECONDS`: timeout fetch per URL
- `SCRAPE_CHUNK_SIZE`: ukuran maksimum chunk (karakter)
- `SCRAPE_CHUNK_OVERLAP`: overlap antar chunk
- `SCRAPE_MIN_TEXT_LENGTH`: minimum panjang teks agar halaman dianggap valid
- `SCRAPE_FOLLOW_LINKS`: `true/false`, untuk URL listing/news page, ikuti link artikel terkait
- `SCRAPE_MAX_LINKS_PER_URL`: jumlah link artikel turunan per URL awal
- `SCRAPE_MAX_TOTAL_URLS`: batas total URL yang di-crawl
- `RETRIEVER_TOP_K`: jumlah chunk kandidat yang dipakai retriever
- `RETRIEVER_CANDIDATE_MULTIPLIER`: pengali kandidat sebelum diseleksi diversitas sumber
- `RETRIEVER_LEXICAL_WEIGHT`: bobot kecocokan keyword (0.0 - 1.0)
- `RETRIEVER_MAX_PER_SOURCE`: maksimal chunk dari sumber URL yang sama agar konteks lebih beragam
- `MAX_CONTEXT_CHARS`: batas panjang konteks yang dikirim ke model
- `NEWS_MAX_STORIES`: jumlah maksimum artikel berita unik untuk query berita
- `SHOW_RETRIEVED_CONTEXT`: `true/false`, menampilkan konteks mentah ke terminal atau tidak

## Smoke test scraper (opsional)

```bash
uv run python -c "from service.scraper_service import ScraperService; pages=ScraperService.scrape(['https://example.com'], timeout_seconds=10, min_text_length=20); docs=ScraperService.to_documents(pages, chunk_size=200, chunk_overlap=40); print(f'pages={len(pages)} docs={len(docs)}')"
```
