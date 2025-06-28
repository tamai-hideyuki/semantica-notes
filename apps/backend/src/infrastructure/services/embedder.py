import os
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer

class EmbedderService:
    def __init__(self, model_name: str = None):
        model_name = model_name or os.getenv("MODEL_NAME", "sentence-transformers/LaBSE")
        # スレッド制御
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        emb = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False
        ).astype("float32")
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        return emb / np.clip(norms, a_min=1e-12, a_max=None)
