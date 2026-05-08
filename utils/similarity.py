import numpy as np
from numpy.typing import NDArray

def cosine_similarity(a : NDArray[np.float64], b : NDArray[np.float64]) -> float:
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
