import numpy as np
from numpy.typing import NDArray

def cosine_similarity(a : NDArray[np.float64], b : NDArray[np.float64]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    PURPOSE / TUJUAN:
    - EN: Measures the angular distance between two vectors, returning a value between -1 and 1 (typically 0 to 1 for unit vectors).
    - ID: Mengukur jarak sudut antara dua vektor, mengembalikan nilai antara -1 dan 1 (biasanya 0 hingga 1 untuk vektor unit).
    
    PARAMS / PARAMETER:
    - a (NDArray[np.float64]): First vector / Vektor pertama
    - b (NDArray[np.float64]): Second vector / Vektor kedua
    
    RETURNS / HASIL:
    - float: Cosine similarity value / Nilai kesamaan cosine
      - 1.0 = identical vectors / vektor identik
      - 0.0 = orthogonal vectors / vektor ortogonal
      - -1.0 = opposite vectors / vektor berlawanan
    
    FORMULA / RUMUS:
    cos_sim(a, b) = (a · b) / (||a|| × ||b||)
    where · is dot product and || || is L2 norm
    
    USE CASE / KASUS PENGGUNAAN:
    - Measuring semantic similarity between text embeddings / Mengukur kesamaan semantik antara embedding teks
    - Ranking documents by relevance to a query / Mengurutkan dokumen berdasarkan relevansi dengan kueri
    - Finding similar items in vector space / Menemukan item serupa dalam ruang vektor
    
    EXAMPLE / CONTOH:
    import numpy as np
    a = np.array([1, 0, 0])
    b = np.array([1, 0, 0])
    result = cosine_similarity(a, b)  # Returns 1.0 (identical)
    
    c = np.array([0, 1, 0])
    result = cosine_similarity(a, c)  # Returns 0.0 (orthogonal)
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
