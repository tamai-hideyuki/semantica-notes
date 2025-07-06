import os
import numpy as np
from typing import List, Tuple, Union
from sentence_transformers import SentenceTransformer

class EmbedderService:
    def __init__(self, model_name: str | None = None):
        model_name = model_name or os.getenv("MODEL_NAME", "sentence-transformers/LaBSE")
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: Union[str, List[str]]) -> np.ndarray:
        # 単一文字列ならリスト化して最後に剥がすフラグを立てる
        single = False
        if isinstance(texts, str):
            texts = [texts]
            single = True

        # モデルで常にバッチ（2D）を返してもらう
        emb = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=False
        ).astype("float32")  # shape = (batch, dim)

        # 2D 前提で正規化
        norms = np.linalg.norm(emb, axis=1, keepdims=True)
        emb = emb / np.clip(norms, a_min=1e-12, a_max=None)

        # 単一入力なら 1D に戻して返す
        return emb[0] if single else emb

    def chunk_text(self, text: str, max_length: int = 500) -> List[str]:
        """
        本文を max_length 文字以下のチャンクに分割
        """
        chunks: List[str] = []
        current = ""
        for line in text.splitlines(keepends=True):
            if len(current) + len(line) <= max_length:
                current += line
            else:
                chunks.append(current.strip())
                current = line
        if current.strip():
            chunks.append(current.strip())
        return chunks

    def encode_chunks(
        self,
        text: str,
        max_length: int = 500
    ) -> List[Tuple[str, np.ndarray]]:
        """
        1) text をチャンクに分割
        2) 各チャンクをベクトル化
        → List[(chunk_text, vector)]
        """
        chunks = self.chunk_text(text, max_length)
        embeddings = self.encode(chunks)  # np.ndarray, shape=(n_chunks, dim)
        return list(zip(chunks, embeddings))
