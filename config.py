import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _parse_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} harus berupa angka bulat. Nilai saat ini: '{raw_value}'") from exc


def _parse_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} harus berupa angka desimal. Nilai saat ini: '{raw_value}'") from exc


def _parse_list_env(name: str) -> list[str]:
    raw_value = os.getenv(name, "")
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def _parse_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise RuntimeError(
        f"{name} harus boolean (true/false, 1/0, yes/no). Nilai saat ini: '{raw_value}'"
    )

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "API key tidak ditemukan. Set OPENROUTER_API_KEY atau OPENAI_API_KEY terlebih dulu."
    )

client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "google/gemini-2.5-flash-preview:free")

SCRAPE_URLS = _parse_list_env("SCRAPE_URLS")
SCRAPE_TIMEOUT_SECONDS = _parse_int_env("SCRAPE_TIMEOUT_SECONDS", 15)
SCRAPE_CHUNK_SIZE = _parse_int_env("SCRAPE_CHUNK_SIZE", 800)
SCRAPE_CHUNK_OVERLAP = _parse_int_env("SCRAPE_CHUNK_OVERLAP", 120)
SCRAPE_MIN_TEXT_LENGTH = _parse_int_env("SCRAPE_MIN_TEXT_LENGTH", 250)
SCRAPE_FOLLOW_LINKS = _parse_bool_env("SCRAPE_FOLLOW_LINKS", True)
SCRAPE_MAX_LINKS_PER_URL = _parse_int_env("SCRAPE_MAX_LINKS_PER_URL", 6)
SCRAPE_MAX_TOTAL_URLS = _parse_int_env("SCRAPE_MAX_TOTAL_URLS", 40)

RETRIEVER_TOP_K = _parse_int_env("RETRIEVER_TOP_K", 6)
RETRIEVER_CANDIDATE_MULTIPLIER = _parse_int_env("RETRIEVER_CANDIDATE_MULTIPLIER", 5)
RETRIEVER_LEXICAL_WEIGHT = _parse_float_env("RETRIEVER_LEXICAL_WEIGHT", 0.2)
RETRIEVER_MAX_PER_SOURCE = _parse_int_env("RETRIEVER_MAX_PER_SOURCE", 3)
MAX_CONTEXT_CHARS = _parse_int_env("MAX_CONTEXT_CHARS", 12000)
NEWS_MAX_STORIES = _parse_int_env("NEWS_MAX_STORIES", 8)
SHOW_RETRIEVED_CONTEXT = _parse_bool_env("SHOW_RETRIEVED_CONTEXT", False)

if SCRAPE_MAX_LINKS_PER_URL < 0:
    raise RuntimeError("SCRAPE_MAX_LINKS_PER_URL tidak boleh negatif")
if SCRAPE_MAX_TOTAL_URLS <= 0:
    raise RuntimeError("SCRAPE_MAX_TOTAL_URLS harus > 0")
if RETRIEVER_CANDIDATE_MULTIPLIER <= 0:
    raise RuntimeError("RETRIEVER_CANDIDATE_MULTIPLIER harus > 0")
if not 0 <= RETRIEVER_LEXICAL_WEIGHT <= 1:
    raise RuntimeError("RETRIEVER_LEXICAL_WEIGHT harus di antara 0.0 sampai 1.0")
if RETRIEVER_MAX_PER_SOURCE <= 0:
    raise RuntimeError("RETRIEVER_MAX_PER_SOURCE harus > 0")
if MAX_CONTEXT_CHARS <= 0:
    raise RuntimeError("MAX_CONTEXT_CHARS harus > 0")
if NEWS_MAX_STORIES <= 0:
    raise RuntimeError("NEWS_MAX_STORIES harus > 0")
