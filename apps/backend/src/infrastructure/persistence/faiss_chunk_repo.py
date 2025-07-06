import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Set

import faiss
import numpy as np
from domain.memo import Memo

logger = logging.getLogger(__name__)

class FaissChunkRepository:
    """
    チャンク単位の FAISS インデックス管理リポジトリ
    - チャンクID の重複を防止
    - ID マッピングはセットで管理して永続化
    """

    def __init__(self, index_dir: Path, dimension: int):
        self.index_dir = index_dir
        self.dimension = dimension
        # インデックスと ID セットをロード
        self.index = self._load_or_create_index()
        self._chunk_id_set = set(self._load_chunk_ids())

    def _load_or_create_index(self) -> faiss.IndexFlatIP:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        index_path = self.index_dir / "chunk.index"
        if index_path.exists():
            idx = faiss.read_index(str(index_path))
            logger.debug("Loaded FAISS chunk index: %s (ntotal=%d)", index_path, idx.ntotal)
            return idx
        idx = faiss.IndexFlatIP(self.dimension)
        logger.debug("Created new FAISS IndexFlatIP(dim=%d)", self.dimension)
        return idx

    def _load_chunk_ids(self) -> List[str]:
        ids_path = self.index_dir / "chunk_ids.json"
        if ids_path.exists():
            try:
                with open(ids_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to load chunk_ids.json: %s", e)
        return []

    def _save_chunk_ids(self) -> None:
        ids_path = self.index_dir / "chunk_ids.json"
        try:
            with open(ids_path, "w", encoding="utf-8") as f:
                json.dump(list(self._chunk_id_set), f, ensure_ascii=False, indent=2)
            logger.debug("Persisted %d chunk IDs", len(self._chunk_id_set))
        except Exception as e:
            logger.error("Failed to save chunk_ids.json: %s", e)

    def _persist_index(self) -> None:
        index_path = self.index_dir / "chunk.index"
        try:
            faiss.write_index(self.index, str(index_path))
            logger.debug("Persisted FAISS index to %s", index_path)
        except Exception as e:
            logger.error("Failed to write FAISS index: %s", e)

    def save(self) -> None:
        """
        FAISS インデックスと ID マッピングを永続化
        """
        self._persist_index()
        self._save_chunk_ids()

    def add_chunks_batch(
        self,
        items: List[Tuple[str, np.ndarray]]
    ) -> None:
        """
        バッチ単位でチャンクを追加し、一度だけ永続化
        """
        # 重複排除して新規アイテムだけ処理
        new_items = [(cid, vec) for cid, vec in items if cid not in self._chunk_id_set]
        if not new_items:
            logger.debug("No new chunks to add")
            return
        vectors = np.stack([vec for _, vec in new_items])
        self.index.add(vectors)
        for chunk_id, _ in new_items:
            self._chunk_id_set.add(chunk_id)
        # 一括で保存
        self.save()

    def add_chunks(
        self,
        items: List[Tuple[str, np.ndarray]]
    ) -> None:
        """
        items: List of (chunk_id, vector)
        単体追加呼び出し時もバッチ方式を利用
        """
        self.add_chunks_batch(items)

    def search(self, query_vec: np.ndarray, top_k: int) -> List[Tuple[str, float]]:
        """
        return List of (chunk_id, score)
        """
        total = int(self.index.ntotal)
        if total <= 0:
            return []
        top_k = min(top_k, total)
        D, I = self.index.search(query_vec.reshape(1, -1), top_k)
        results: List[Tuple[str, float]] = []
        for idx, score in zip(I[0], D[0]):
            if idx < 0:
                continue
            cid = self._get_chunk_id(idx)
            if cid:
                results.append((cid, float(score)))
        return results

    def _get_chunk_id(self, index: int) -> Optional[str]:
        """
        インデックス番号からチャンクIDを逆引き
        """
        try:
            return list(self._chunk_id_set)[index]
        except Exception:
            logger.warning("Invalid chunk index: %d", index)
            return None

    async def filter_new(self, memos: List[Memo]) -> List[Memo]:
        """
        まだベクトル化されていないメモだけを返す
        """
        existing_uuids: Set[str] = {cid.split("_", 1)[0] for cid in self._chunk_id_set}
        return [m for m in memos if m.uuid not in existing_uuids]
