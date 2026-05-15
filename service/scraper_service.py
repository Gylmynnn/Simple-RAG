from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, Tag


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

NOISE_SELECTORS : list[str] = [
    "script",
    "style",
    "noscript",
    "svg",
    "form",
    "nav",
    "footer",
    "header",
    "aside",
    "sup.reference",
    ".mw-editsection",
    ".reflist",
    ".reference",
    ".references",
    ".toc",
    "#toc",
    ".vector-toc",
    ".navbox",
    ".metadata",
    ".infobox",
    ".sidebar",
    ".hatnote",
    ".shortdescription",
    ".mw-references-wrap",
]

STOP_HEADINGS = {
    "see also",
    "references",
    "notes",
    "citations",
    "further reading",
    "external links",
    "bibliography",
    "sources",
}

NOISE_PARENT_CLASSES = {
    "toc",
    "reference",
    "references",
    "reflist",
    "navbox",
    "sidebar",
    "infobox",
    "metadata",
    "mw-references-wrap",
}

NOISE_PARENT_CLASS_PREFIXES = (
    "toc-",
    "navbox-",
    "sidebar-",
    "infobox-",
    "reference-",
    "references-",
    "mw-references",
)

LISTING_URL_HINTS = {
    "latest",
    "news",
    "headline",
    "headlines",
    "top",
    "updates",
    "update",
    "category",
    "section",
    "stories",
}

BLOCKED_LINK_KEYWORDS = {
    "/video",
    "/videos",
    "/podcast",
    "/audio",
    "/gallery",
    "/photo",
    "/search",
    "/tag/",
    "/tags/",
    "/topic/",
    "/topics/",
    "/category/",
    "/categories/",
    "/about",
    "/contact",
    "/privacy",
    "/terms",
    "/cookies",
    "/account",
    "/signin",
    "/login",
    "/subscribe",
    "/newsletter",
}

BLOCKED_LINK_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".pdf",
    ".zip",
    ".mp4",
    ".mp3",
)


@dataclass
class ScrapedPage:
    """
    Dataclass representing a scraped web page with extracted content.
    
    PURPOSE / TUJUAN:
    - EN: Holds structured data about a scraped web page including URL, title, text content, and optional publication date.
    - ID: Menyimpan data terstruktur tentang halaman web yang di-scrape termasuk URL, judul, konten teks, dan tanggal publikasi opsional.
    """
    url: str
    """The source URL of the scraped page / URL sumber halaman yang di-scrape"""
    
    title: str
    """The title/heading of the page / Judul/heading halaman"""
    
    text: str
    """The main text content extracted from the page / Konten teks utama yang diekstrak dari halaman"""
    
    published_at: str | None = None
    """Optional publication date/timestamp of the page / Tanggal publikasi/timestamp halaman opsional"""


class ScraperService:
    """
    Service for scraping and extracting content from web pages.
    
    PURPOSE / TUJUAN:
    - EN: Handles web scraping, HTML parsing, and text extraction to convert web pages into clean text documents.
    - ID: Menangani web scraping, parsing HTML, dan ekstraksi teks untuk mengubah halaman web menjadi dokumen teks yang bersih.
    
    FEATURES / FITUR:
    - Basic scraping of specific URLs / Scraping dasar URL spesifik
    - Link discovery and recursive scraping / Penemuan tautan dan scraping rekursif
    - HTML noise removal and text cleaning / Penghapusan kebisingan HTML dan pembersihan teks
    - Text chunking with overlap for document processing / Pemberian chunk teks dengan overlap untuk pemrosesan dokumen
    - Duplicate detection and deduplication / Deteksi duplikat dan deduplikasi
    """
    
    @staticmethod
    def scrape(urls: list[str], timeout_seconds: int, min_text_length: int) -> list[ScrapedPage]:
        """
        Scrape specified URLs without following links.
        
        PURPOSE / TUJUAN:
        - EN: Simple scraping method that only scrapes the provided URLs without discovering or following links.
        - ID: Metode scraping sederhana yang hanya mem-scrape URL yang disediakan tanpa menemukan atau mengikuti tautan.
        
        PARAMS / PARAMETER:
        - urls (list[str]): List of URLs to scrape / Daftar URL untuk di-scrape
        - timeout_seconds (int): Network timeout for each request / Batas waktu jaringan untuk setiap permintaan
        - min_text_length (int): Minimum text length to keep a page / Panjang teks minimum untuk menyimpan halaman
        
        RETURNS / HASIL:
        - list[ScrapedPage]: List of successfully scraped pages / Daftar halaman yang berhasil di-scrape
        
        EXAMPLE / CONTOH:
        pages = ScraperService.scrape(
            urls=["https://example.com"],
            timeout_seconds=15,
            min_text_length=250
        )
        """
        return ScraperService.scrape_expanded(
            urls=urls,
            timeout_seconds=timeout_seconds,
            min_text_length=min_text_length,
            follow_links=False,
            max_links_per_url=0,
            max_total_urls=max(1, len(urls)),
        )

    @staticmethod
    def scrape_expanded(
        urls: list[str],
        timeout_seconds: int,
        min_text_length: int,
        follow_links: bool,
        max_links_per_url: int,
        max_total_urls: int,
    ) -> list[ScrapedPage]:
        """
        Advanced scraping with link discovery and recursive scraping.
        
        PURPOSE / TUJUAN:
        - EN: Scrapes URLs and optionally follows links within them to expand the dataset. Uses BFS to discover and scrape related pages.
        - ID: Mem-scrape URL dan secara opsional mengikuti tautan di dalamnya untuk memperluas dataset. Menggunakan BFS untuk menemukan dan mem-scrape halaman terkait.
        
        PARAMS / PARAMETER:
        - urls (list[str]): Initial list of URLs to scrape / Daftar awal URL untuk di-scrape
        - timeout_seconds (int): Network timeout per request / Batas waktu jaringan per permintaan
        - min_text_length (int): Minimum text length to keep a page / Panjang teks minimum untuk menyimpan halaman
        - follow_links (bool): Whether to discover and follow links from scraped pages / Apakah akan menemukan dan mengikuti tautan dari halaman yang di-scrape
        - max_links_per_url (int): Maximum number of links to extract from each page / Jumlah maksimal tautan yang akan diekstrak dari setiap halaman
        - max_total_urls (int): Maximum total URLs to scrape / Jumlah URL total maksimal untuk di-scrape
        
        RETURNS / HASIL:
        - list[ScrapedPage]: List of successfully scraped pages (up to max_total_urls) / Daftar halaman yang berhasil di-scrape (hingga max_total_urls)
        
        RAISES / MELEMPAR:
        - ValueError: If max_total_urls <= 0 or max_links_per_url < 0 / Jika max_total_urls <= 0 atau max_links_per_url < 0
        
        ALGORITHM / ALGORITMA:
        - Uses BFS (Breadth-First Search) with a queue to manage URLs / Menggunakan BFS (Pencarian Breadth-First) dengan antrian untuk mengelola URL
        - Identifies listing URLs (home, category, latest) for link discovery / Mengidentifikasi URL listing (home, kategori, terbaru) untuk penemuan tautan
        - Respects max_total_urls and max_links_per_url limits / Menghormati batas max_total_urls dan max_links_per_url
        - Filters out duplicates, invalid pages, and blocked link patterns / Menyaring duplikat, halaman tidak valid, dan pola tautan yang diblokir
        """
        if max_total_urls <= 0:
            raise ValueError("max_total_urls harus > 0")
        if max_links_per_url < 0:
            raise ValueError("max_links_per_url tidak boleh negatif")

        pages: list[ScrapedPage] = []
        seen_urls: set[str] = set()
        queue: deque[tuple[str, bool]] = deque()

        for url in urls:
            try:
                normalized_url = _normalize_url(url)
            except ValueError as exc:
                print(f"[scraper] skip {url}: {exc}")
                continue

            queue.append((normalized_url, _is_listing_url(normalized_url)))

        while queue and len(seen_urls) < max_total_urls:
            current_url, discover_links = queue.popleft()

            if current_url in seen_urls:
                continue

            seen_urls.add(current_url)

            try:
                html = _download_html(url=current_url, timeout_seconds=timeout_seconds)
                page = _parse_html(url=current_url, html=html)
            except (HTTPError, URLError, ValueError) as exc:
                print(f"[scraper] skip {current_url}: {exc}")
                continue
            except Exception as exc:
                print(f"[scraper] unexpected error {current_url}: {exc}")
                continue

            if len(page.text) < min_text_length:
                print(
                    f"[scraper] skip {current_url}: teks terlalu pendek "
                    f"({len(page.text)} chars, min {min_text_length})"
                )
            else:
                pages.append(page)
                print(f"[scraper] loaded {current_url} ({len(page.text)} chars)")

            if not follow_links:
                continue
            if not discover_links:
                continue
            if max_links_per_url == 0:
                continue
            if len(seen_urls) >= max_total_urls:
                continue

            linked_urls = _extract_candidate_links(
                base_url=current_url,
                html=html,
                max_links=max_links_per_url,
                existing_urls=seen_urls,
            )

            for linked_url in linked_urls:
                if len(seen_urls) + len(queue) >= max_total_urls:
                    break
                queue.append((linked_url, False))

        return pages

    @staticmethod
    def to_documents(
        pages: Iterable[ScrapedPage],
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[str]:
        """
        Convert scraped pages into chunked documents with metadata.
        
        PURPOSE / TUJUAN:
        - EN: Splits scraped pages into overlapping chunks for RAG processing, preserving metadata and deduplicating.
        - ID: Membagi halaman yang di-scrape menjadi chunk yang tumpang tindih untuk pemrosesan RAG, melestarikan metadata dan deduplikasi.
        
        PARAMS / PARAMETER:
        - pages (Iterable[ScrapedPage]): Scraped pages to process / Halaman yang di-scrape untuk diproses
        - chunk_size (int): Target size of each text chunk in characters / Ukuran target setiap chunk teks dalam karakter
        - chunk_overlap (int): Number of characters to overlap between chunks / Jumlah karakter untuk tumpang tindih antar chunk
        
        RETURNS / HASIL:
        - list[str]: List of formatted documents with metadata headers / Daftar dokumen yang diformat dengan header metadata
        
        RAISES / MELEMPAR:
        - ValueError: If chunk_size <= 0, chunk_overlap < 0, or chunk_overlap >= chunk_size / Jika chunk_size <= 0, chunk_overlap < 0, atau chunk_overlap >= chunk_size
        
        DOCUMENT FORMAT / FORMAT DOKUMEN:
        Each document has metadata followed by chunk text:
        Sumber: {url}
        Judul: {title}
        Terbit: {published_at}  (optional)
        Bagian: {chunk_number}/{total_chunks}
        
        {chunk_text}
        
        EXAMPLE / CONTOH:
        pages = [ScrapedPage(url="...", title="...", text="...")]
        docs = ScraperService.to_documents(pages, chunk_size=800, chunk_overlap=120)
        """
        if chunk_size <= 0:
            raise ValueError("SCRAPE_CHUNK_SIZE harus > 0")
        if chunk_overlap < 0:
            raise ValueError("SCRAPE_CHUNK_OVERLAP tidak boleh negatif")
        if chunk_overlap >= chunk_size:
            raise ValueError("SCRAPE_CHUNK_OVERLAP harus lebih kecil dari SCRAPE_CHUNK_SIZE")

        documents: list[str] = []
        seen_chunks: set[tuple[str, str]] = set()

        for page in pages:
            chunks = _chunk_text(
                text=page.text,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            total = len(chunks)
            for index, chunk in enumerate(chunks, start=1):
                dedupe_key = (page.url, chunk)
                if dedupe_key in seen_chunks:
                    continue

                seen_chunks.add(dedupe_key)
                metadata = [
                    f"Sumber: {page.url}",
                    f"Judul: {page.title}",
                ]
                if page.published_at:
                    metadata.append(f"Terbit: {page.published_at}")
                metadata.append(f"Bagian: {index}/{total}")

                documents.append(
                    "\n".join(
                        [
                            *metadata,
                            "",
                            chunk,
                        ]
                    )
                )

        return documents


def _normalize_url(url: str) -> str:
    """
    Normalize and validate a URL.
    
    PURPOSE / TUJUAN:
    - EN: Validates that a URL has proper HTTP(S) scheme and netloc, returns normalized URL.
    - ID: Memvalidasi bahwa URL memiliki skema HTTP(S) dan netloc yang tepat, mengembalikan URL yang dinormalisasi.
    
    PARAMS / PARAMETER:
    - url (str): Raw URL string to normalize / String URL mentah untuk dinormalisasi
    
    RETURNS / HASIL:
    - str: Normalized URL / URL yang dinormalisasi
    
    RAISES / MELEMPAR:
    - ValueError: If URL is invalid (missing scheme or netloc) / Jika URL tidak valid (skema atau netloc hilang)
    """
    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL tidak valid. Gunakan format http:// atau https://")
    return normalized


def _download_html(url: str, timeout_seconds: int) -> str:
    """
    Download and return HTML content from a URL.
    
    PURPOSE / TUJUAN:
    - EN: Fetches HTML from a URL with proper User-Agent headers, validates content type, and handles encoding.
    - ID: Mengambil HTML dari URL dengan header User-Agent yang tepat, memvalidasi tipe konten, dan menangani encoding.
    
    PARAMS / PARAMETER:
    - url (str): URL to download / URL untuk diunduh
    - timeout_seconds (int): Network timeout in seconds / Batas waktu jaringan dalam detik
    
    RETURNS / HASIL:
    - str: HTML content as string / Konten HTML sebagai string
    
    RAISES / MELEMPAR:
    - ValueError: If content is not HTML (wrong Content-Type) or if HTML is empty / Jika konten bukan HTML atau jika HTML kosong
    - URLError: If network request fails / Jika permintaan jaringan gagal
    - HTTPError: If HTTP status code indicates error / Jika kode status HTTP menunjukkan kesalahan
    
    FEATURES / FITUR:
    - Sets User-Agent header to avoid blocking / Menetapkan header User-Agent untuk menghindari pemblokiran
    - Validates Content-Type is text/html or application/xhtml+xml / Memvalidasi Content-Type adalah text/html atau application/xhtml+xml
    - Auto-detects charset from response headers / Auto-mendeteksi charset dari header respons
    - Falls back to UTF-8 if charset detection fails / Kembali ke UTF-8 jika deteksi charset gagal
    """
    request = Request(
        url=url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )

    with urlopen(request, timeout=timeout_seconds) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise ValueError(f"bukan halaman HTML (Content-Type: {content_type or 'unknown'})")

        raw_html = response.read()
        encoding = response.headers.get_content_charset() or "utf-8"

    try:
        return raw_html.decode(encoding, errors="replace")
    except LookupError:
        return raw_html.decode("utf-8", errors="replace")


def _parse_html(url: str, html: str) -> ScrapedPage:
    """
    Parse HTML content and extract clean text, title, and publication date.
    
    PURPOSE / TUJUAN:
    - EN: Parses HTML using BeautifulSoup, removes noise elements, extracts main content, title, and metadata.
    - ID: Mem-parse HTML menggunakan BeautifulSoup, menghapus elemen noise, mengekstrak konten utama, judul, dan metadata.
    
    PARAMS / PARAMETER:
    - url (str): Source URL (used as fallback title) / URL sumber (digunakan sebagai judul fallback)
    - html (str): Raw HTML content / Konten HTML mentah
    
    RETURNS / HASIL:
    - ScrapedPage: Structured page data with url, title, text, published_at / Data halaman terstruktur dengan url, judul, teks, published_at
    
    RAISES / MELEMPAR:
    - ValueError: If no content root found or content is empty after cleaning / Jika akar konten tidak ditemukan atau konten kosong setelah pembersihan
    
    PROCESSING STEPS / LANGKAH PEMROSESAN:
    1. Remove noise elements (scripts, styles, ads, etc.) / Hapus elemen noise (script, style, iklan, dll)
    2. Find content root (Wikipedia, main tag, article tag, body) / Temukan akar konten
    3. Extract title from h1, page title, or h2 / Ekstrak judul dari h1, judul halaman, atau h2
    4. Extract published date from meta tags or time elements / Ekstrak tanggal publikasi dari meta tag atau elemen waktu
    5. Extract text blocks (paragraphs, list items) and remove inline noise / Ekstrak blok teks dan hapus kebisingan inline
    6. Normalize and deduplicate blocks / Normalisasi dan deduplikasi blok
    """
    soup = BeautifulSoup(html, "html.parser")
    _remove_noise_nodes(soup)

    content_root = _select_content_root(soup)
    title = _extract_title(soup, content_root, url)
    published_at = _extract_published_at(soup)
    blocks = _extract_text_blocks(content_root)
    cleaned_text = _normalize_blocks(blocks)

    if not cleaned_text:
        raise ValueError("konten kosong setelah dibersihkan")

    return ScrapedPage(url=url, title=title, text=cleaned_text, published_at=published_at)


def _remove_noise_nodes(soup: BeautifulSoup) -> None:
    for selector in NOISE_SELECTORS:
        for node in soup.select(selector):
            node.decompose()


def _select_content_root(soup: BeautifulSoup) -> Tag:
    root = (
        soup.select_one("#mw-content-text .mw-parser-output")
        or soup.select_one("main")
        or soup.select_one("article")
        or soup.body
    )

    if root is None:
        raise ValueError("gagal menemukan root konten")

    return root


def _extract_title(soup: BeautifulSoup, content_root: Tag, fallback_url: str) -> str:
    heading = soup.select_one("#firstHeading") or content_root.find(["h1", "h2"])
    if heading is not None and heading.name == "h1":
        heading_text = _normalize_whitespace(heading.get_text(separator=" ", strip=True))
        if heading_text:
            return heading_text

    if soup.title and soup.title.string:
        title_text = _normalize_whitespace(soup.title.string)
        title_text = re.sub(r"\s*-\s*wikipedia\s*$", "", title_text, flags=re.IGNORECASE)
        if title_text:
            return title_text

    if heading is not None:
        heading_text = _normalize_whitespace(heading.get_text(separator=" ", strip=True))
        if heading_text:
            return heading_text

    return fallback_url


def _extract_published_at(soup: BeautifulSoup) -> str | None:
    selectors = [
        "meta[property='article:published_time']",
        "meta[name='article:published_time']",
        "meta[property='og:updated_time']",
        "meta[name='pubdate']",
        "meta[name='publishdate']",
        "meta[name='date']",
        "time[datetime]",
    ]

    for selector in selectors:
        node = soup.select_one(selector)
        if node is None:
            continue

        value = node.get("content") or node.get("datetime") or node.get_text(separator=" ", strip=True)
        normalized = _normalize_whitespace(value)
        if normalized:
            return normalized

    return None


def _extract_text_blocks(content_root: Tag) -> list[str]:
    blocks: list[str] = []

    for tag in content_root.find_all(["h2", "h3", "p", "li"]):
        if not isinstance(tag, Tag):
            continue
        if _has_noise_parent(tag):
            continue

        if tag.name in {"h2", "h3"}:
            heading = _normalize_whitespace(tag.get_text(separator=" ", strip=True)).lower()
            heading = _clean_inline_noise(heading)
            if heading in STOP_HEADINGS:
                break
            continue

        text = _normalize_whitespace(tag.get_text(separator=" ", strip=True))
        text = _clean_inline_noise(text)
        if len(text) < 40:
            continue

        blocks.append(text)

    return blocks


def _has_noise_parent(tag: Tag) -> bool:
    for parent in tag.parents:
        if not isinstance(parent, Tag):
            continue

        for class_name in parent.get("class", []):
            normalized = class_name.lower()
            if normalized in NOISE_PARENT_CLASSES:
                return True
            if any(normalized.startswith(prefix) for prefix in NOISE_PARENT_CLASS_PREFIXES):
                return True

    return False


def _normalize_blocks(blocks: list[str]) -> str:
    deduped: list[str] = []
    seen: set[str] = set()

    for block in blocks:
        normalized = _normalize_whitespace(block)
        if not normalized:
            continue
        if normalized in seen:
            continue

        seen.add(normalized)
        deduped.append(normalized)

    return "\n\n".join(deduped)


def _is_listing_url(url: str) -> bool:
    parsed = urlparse(url)
    tokens = [token for token in re.split(r"[^a-zA-Z0-9]+", parsed.path.lower()) if token]
    query_tokens = [token for token in re.split(r"[^a-zA-Z0-9]+", parsed.query.lower()) if token]

    if any(token in LISTING_URL_HINTS for token in tokens):
        return True
    if any(token in LISTING_URL_HINTS for token in query_tokens):
        return True

    return parsed.path in {"", "/"}


def _extract_candidate_links(
    base_url: str,
    html: str,
    max_links: int,
    existing_urls: set[str],
) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    base_host = urlparse(base_url).netloc.lower()
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        if not isinstance(anchor, Tag):
            continue

        href = anchor.get("href", "").strip()
        if not href:
            continue

        absolute = _normalize_link(base_url, href)
        if not absolute:
            continue
        if absolute in existing_urls or absolute in seen:
            continue

        parsed = urlparse(absolute)
        if parsed.netloc.lower() != base_host:
            continue
        if _is_blocked_link(parsed):
            continue

        anchor_text = _normalize_whitespace(anchor.get_text(separator=" ", strip=True)).lower()
        score = _score_candidate_link(parsed.path.lower(), anchor_text)
        if score <= 0:
            continue

        seen.add(absolute)
        candidates.append((score, absolute))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [url for _, url in candidates[:max_links]]


def _normalize_link(base_url: str, href: str) -> str | None:
    joined = urljoin(base_url, href)
    joined, _ = urldefrag(joined)
    parsed = urlparse(joined)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    query = parsed.query
    if query:
        query = "&".join(part for part in query.split("&") if not part.lower().startswith("utm_"))

    normalized = parsed._replace(query=query)
    normalized_url = normalized.geturl().rstrip("/")
    return normalized_url


def _is_blocked_link(parsed) -> bool:
    path = parsed.path.lower()

    if path.endswith(BLOCKED_LINK_EXTENSIONS):
        return True
    if any(keyword in path for keyword in BLOCKED_LINK_KEYWORDS):
        return True
    if path in {"", "/"}:
        return True

    return False


def _score_candidate_link(path: str, anchor_text: str) -> int:
    score = 0

    if any(token in path for token in ["/202", "/story", "/article", "/politics", "/business", "/world", "/tech"]):
        score += 5
    if any(token in anchor_text for token in ["breaking", "latest", "news", "update"]):
        score += 5

    depth = len([part for part in path.split("/") if part])
    if depth >= 2:
        score += 2

    if len(anchor_text) >= 20:
        score += 1

    return score


def _clean_inline_noise(text: str) -> str:
    cleaned = re.sub(r"\[[0-9]+\]", "", text)
    cleaned = re.sub(r"\[(citation needed|note [0-9]+|clarification needed)\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Split text into overlapping chunks while preserving paragraph boundaries.
    
    PURPOSE / TUJUAN:
    - EN: Intelligently chunks text by paragraphs first, then splits large paragraphs by sentences/words to achieve target size.
    - ID: Secara cerdas mem-chunk teks berdasarkan paragraf terlebih dahulu, kemudian membagi paragraf besar berdasarkan kalimat/kata untuk mencapai ukuran target.
    
    PARAMS / PARAMETER:
    - text (str): Text to chunk / Teks untuk di-chunk
    - chunk_size (int): Target size of each chunk in characters / Ukuran target setiap chunk dalam karakter
    - chunk_overlap (int): Number of characters to overlap between chunks / Jumlah karakter untuk tumpang tindih antar chunk
    
    RETURNS / HASIL:
    - list[str]: List of text chunks / Daftar chunk teks
    
    CHUNKING STRATEGY / STRATEGI CHUNKING:
    1. Split by double newlines (paragraph boundaries) / Pisahkan oleh double newline (batas paragraf)
    2. For large paragraphs (> chunk_size), recursively split by sentences / Untuk paragraf besar, secara rekursif pisahkan berdasarkan kalimat
    3. Combine paragraphs while respecting chunk_size / Gabungkan paragraf sambil menghormati chunk_size
    4. Create overlap from end of previous chunk / Buat overlap dari akhir chunk sebelumnya
    5. Overlap uses previous paragraphs to maintain context / Overlap menggunakan paragraf sebelumnya untuk mempertahankan konteks
    
    EXAMPLE / CONTOH:
    text = "Para 1...\\n\\nPara 2...\\n\\nPara 3..."
    chunks = _chunk_text(text, chunk_size=800, chunk_overlap=120)
    # Returns chunks that start with context from previous chunk
    """
    if not text:
        return []

    paragraphs = [item.strip() for item in text.split("\n\n") if item.strip()]
    expanded_paragraphs: list[str] = []

    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            expanded_paragraphs.append(paragraph)
            continue
        expanded_paragraphs.extend(_split_large_paragraph(paragraph, chunk_size))

    chunks: list[str] = []
    current: list[str] = []

    for paragraph in expanded_paragraphs:
        if not current:
            current = [paragraph]
            continue

        candidate = "\n\n".join(current + [paragraph])
        if len(candidate) <= chunk_size:
            current.append(paragraph)
            continue

        chunks.append("\n\n".join(current))
        overlap = _build_overlap(current, chunk_overlap)
        current = overlap + [paragraph]

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def _build_overlap(paragraphs: list[str], overlap_chars: int) -> list[str]:
    if overlap_chars <= 0:
        return []

    overlap: list[str] = []
    total = 0
    for paragraph in reversed(paragraphs):
        extra = len(paragraph) + (2 if overlap else 0)
        if total + extra > overlap_chars:
            break
        overlap.insert(0, paragraph)
        total += extra

    return overlap


def _split_large_paragraph(paragraph: str, max_chars: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    if len(sentences) <= 1:
        return _split_by_words(paragraph, max_chars)

    pieces: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(sentence) > max_chars:
            if current:
                pieces.append(current)
                current = ""
            pieces.extend(_split_by_words(sentence, max_chars))
            continue

        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                pieces.append(current)
            current = sentence

    if current:
        pieces.append(current)

    return pieces


def _split_by_words(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]

    chunks: list[str] = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = word
            continue

        chunks.extend(word[i : i + max_chars] for i in range(0, len(word), max_chars))

    if current:
        chunks.append(current)

    return chunks
