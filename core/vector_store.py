from service.embedding_service import EmbeddingService


class VectorStore:
    """
    Vector store for managing documents and their embeddings.
    
    PURPOSE / TUJUAN:
    - EN: Stores documents and their vector embeddings for efficient semantic search operations.
    - ID: Menyimpan dokumen dan embedding vektor mereka untuk operasi pencarian semantik yang efisien.
    """
    
    def __init__(self, documents: list[str]) -> None:
        """
        Initialize vector store with documents and compute their embeddings.
        
        PURPOSE / TUJUAN:
        - EN: Creates embeddings for each document using EmbeddingService and stores them alongside documents.
        - ID: Membuat embedding untuk setiap dokumen menggunakan EmbeddingService dan menyimpannya bersama dokumen.
        
        PARAMS / PARAMETER:
        - documents (list[str]): List of documents to embed and store / Daftar dokumen untuk di-embed dan disimpan
        
        ATTRIBUTES / ATRIBUT:
        - self.documents (list[str]): Original documents / Dokumen asli
        - self.embeddings (list): List of embedding vectors for each document / Daftar vektor embedding untuk setiap dokumen
        
        PERFORMANCE NOTES / CATATAN PERFORMA:
        - Warning: Computing embeddings for large document sets can be slow / Peringatan: Menghitung embedding untuk set dokumen besar dapat lambat
        - Each embedding API call may incur costs / Setiap panggilan API embedding dapat menimbulkan biaya
        
        EXAMPLE / CONTOH:
        docs = ["Text 1", "Text 2"]
        store = VectorStore(docs)
        # store.documents = ["Text 1", "Text 2"]
        # store.embeddings = [[0.1, 0.2, ...], [0.3, 0.4, ...]]
        """
        self.documents = documents
        self.embeddings = [EmbeddingService.embed(doc) for doc in documents]
