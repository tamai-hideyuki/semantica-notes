import json
import logging
from pathlib import Path
from typing import Dict, List, Union

import faiss
import numpy as np
from domain.memo import Memo
from interfaces.repositories.index_repo import IndexRepository

logger = logging.getLogger(__name__)


class FaissIndexRepository(IndexRepository):
    """
    FAISS を使ったベクトルインデックスリポジトリ。
    - incremental_update: 未登録メモのみを追加
    - rebuild: 全メモで再構築
    - search: 上位 top_k の UUID リストと距離配列を返却
    """

    def __init__(
        self,
        index_dir: Union[str, Path],
        memo_repo,  # MemoRepository を注入
        dim: int = 768,
    ) -> None:
        # 永続化ディレクトリ
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "faiss.index"
        self.map_path = self.index_dir / "id_to_uuid.json"
        self.dim = dim
        self.memo_repo = memo_repo

        # インデックスの読み込み or 新規作成
        if self.index_path.exists() and self.map_path.exists():
            self.index: faiss.Index = faiss.read_index(str(self.index_path))
            self.id_to_uuid = self._load_id_map()
            logger.debug("Loaded FAISS index (%d entries) & ID map", self.index.ntotal)
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.id_to_uuid: Dict[int, str] = {}
            logger.debug("Created new FAISS IndexFlatL2(dim=%d)", self.dim)

        # 読み込み後の不整合チェック
        if self.index.ntotal != len(self.id_to_uuid):
            logger.warning(
                "Index-map mismatch: ntotal=%d, mapped=%d",
                self.index.ntotal,
                len(self.id_to_uuid),
            )

    def _load_id_map(self) -> Dict[int, str]:
        raw = self.map_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return {int(k): v for k, v in data.items()}

    def _save_id_map(self) -> None:
        payload = {str(k): v for k, v in self.id_to_uuid.items()}
        self.map_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _persist(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        self._save_id_map()
        logger.debug("Persisted FAISS index & ID map")

    def incremental_update(self, memos: List[Memo]) -> None:
        """
        既存にない Memo のみをベクトル化済み embedding から追加登録
        """
        new_memos = [m for m in memos if m.uuid not in self.id_to_uuid.values()]
        if not new_memos:
            logger.debug("No new memos to index")
            return

        vecs = np.stack([m.embedding for m in new_memos]).astype("float32")
        base = self.index.ntotal
        self.index.add(vecs)
        for offset, memo in enumerate(new_memos):
            self.id_to_uuid[base + offset] = memo.uuid

        self._persist()

    def rebuild(self, memos: List[Memo]) -> None:
        """
        全メモを一度クリアして再インデックス化
        """
        self.index = faiss.IndexFlatL2(self.dim)
        self.id_to_uuid.clear()

        if memos:
            vecs = np.stack([m.embedding for m in memos]).astype("float32")
            self.index.add(vecs)
            self.id_to_uuid = {i: m.uuid for i, m in enumerate(memos)}

        self._persist()

    def search(self, query_vec: np.ndarray, top_k: int = 10) -> (List[str], np.ndarray):
        """
        ベクトル検索を同期的に実行し、
        (UUIDリスト, 距離配列) を返却
        """
        q = query_vec.reshape(1, -1).astype("float32")
        dists, ids = self.index.search(q, top_k)
        uuids = [self.id_to_uuid.get(int(i)) for i in ids[0]]
        return uuids, dists[0]
