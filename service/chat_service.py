from config import client, CHAT_MODEL

class ChatService:
    @staticmethod
    def generate(context: str, query: str) -> str | None:
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
