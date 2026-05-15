from config import client, CHAT_MODEL

class ChatService:
    """
    Service for generating responses using LLM with RAG context.
    
    PURPOSE / TUJUAN:
    - EN: Generates contextual responses from an LLM using provided context and user queries.
    - ID: Menghasilkan respons kontekstual dari LLM menggunakan konteks dan kueri pengguna yang disediakan.
    """
    
    @staticmethod
    def generate(context: str, query: str) -> str | None:
        """
        Generate an answer using context and query with LLM.
        
        PURPOSE / TUJUAN:
        - EN: Sends context and user query to an LLM to generate a structured answer based on the provided context.
        - ID: Mengirim konteks dan kueri pengguna ke LLM untuk menghasilkan jawaban terstruktur berdasarkan konteks yang disediakan.
        
        PARAMS / PARAMETER:
        - context (str): Retrieved document context / Konteks dokumen yang diambil
        - query (str): User question or query / Pertanyaan atau kueri pengguna
        
        RETURNS / HASIL:
        - str | None: Generated answer text from LLM, or None if generation fails / Teks jawaban yang dihasilkan dari LLM, atau None jika pembuatan gagal
        
        LLM INSTRUCTIONS / INSTRUKSI LLM:
        The system prompt instructs the model to:
        1. Answer in clear, detailed, structured Indonesian / Menjawab dalam bahasa Indonesia yang jelas, rinci, dan terstruktur
        2. Use only facts from the provided context / Gunakan hanya fakta dari konteks yang disediakan
        3. Explain limitations if context is insufficient / Jelaskan keterbatasan jika konteks tidak cukup
        4. Format as: Core answer → Details (bullets) → Sources (if news) → Context limitations / Format: Inti jawaban → Detail (bullets) → Sumber (jika berita) → Keterbatasan konteks
        
        API USED / API YANG DIGUNAKAN:
        - OpenRouter API via OpenAI client / API OpenRouter melalui klien OpenAI
        - Model: CHAT_MODEL (configurable) / Model: CHAT_MODEL (dapat dikonfigurasi)
        
        EXAMPLE / CONTOH:
        context = "[Konteks 1]\\nSkor: 0.95\\nIni adalah konten dokumen yang relevan..."
        query = "Apa itu AI?"
        answer = ChatService.generate(context, query)
        # Returns structured answer about AI based on context / Mengembalikan jawaban terstruktur tentang AI berdasarkan konteks
        """
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Kamu adalah asisten RAG. Jawab dalam bahasa Indonesia yang jelas, rinci, dan terstruktur. "
                        "Gunakan hanya fakta yang memang ada di konteks. Jika konteks tidak cukup, jelaskan batasannya "
                        "secara eksplisit lalu berikan apa yang bisa disimpulkan."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Gunakan konteks berikut untuk menjawab pertanyaan pengguna.\n\n"
                        f"{context}\n\n"
                        f"Pertanyaan: {query}\n\n"
                        "Format jawaban:\n"
                        "1) Inti jawaban (1 paragraf)\n"
                        "2) Rincian penting (bullet points)\n"
                        "3) Jika pertanyaan tentang berita, tambahkan bagian 'Sumber yang dipakai' berisi judul + URL.\n"
                        "4) Jika data kurang, tambahkan bagian 'Keterbatasan konteks'."
                    ),
                },
            ],
        )
        return response.choices[0].message.content
