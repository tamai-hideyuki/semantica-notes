import json
from pathlib import Path
from typing import List, Tuple, Dict

import faiss
import numpy as np

from domain.memo import Memo
from interfaces.repositories.index_repo import IndexRepository
from interfaces.repositories.memo_repo import MemoRepository


class FaissIndexRepository(IndexRepository):
    def __init__(self, index_dir: Path, memo_repo: MemoRepository, dim: int = 768):
        self.index_dir = index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "faiss.index"
        self.map_path   = self.index_dir / "id_to_uuid.json"
        self.dim = dim

        # インデックスのロード or 新規作成
        if self.index_path.exists():
            self.index = faiss.read_index(str(self.index_path))
        else:
            self.index = faiss.IndexFlatL2(self.dim)

        # 内部ID → UUID マッピングをファイルから復帰
        if self.map_path.exists():
            with open(self.map_path, 'r', encoding='utf-8') as f:
                # JSON のキーは文字列なので int にキャスト
                raw = json.load(f)
                self.id_to_uuid = {int(k): v for k, v in raw.items()}
        else:
            self.id_to_uuid = {}

        self.memo_repo = memo_repo

    def save(self) -> None:
        # 1) index を保存
        faiss.write_index(self.index, str(self.index_path))
        # 2) マッピングも JSON で保存
        with open(self.map_path, 'w', encoding='utf-8') as f:
            json.dump({str(k): v for k, v in self.id_to_uuid.items()}, f, ensure_ascii=False, indent=2)


    def incremental_update(self, memos: List[Memo]) -> None:
        """
        新規メモ分の埋め込みを一括追加し、
        id_to_uuid マッピングを更新して永続化。
        """
        # 1) 埋め込み行列をまとめてスタック
        arr = np.stack([m.embedding for m in memos], axis=0).astype("float32")

        # 2) 既存総数を取得してから追加
        start = int(getattr(self.index, "ntotal", 0))
        self.index.add(arr)

        # 3) マッピング更新
        for offset, memo in enumerate(memos):
            self.id_to_uuid[start + offset] = memo.uuid

        # 4) 永続化
        self.save()

    async def filter_new(self, memos: List[Memo]) -> List[Memo]:
        """
        index に未登録のメモだけを返す
        """
        existing = set(self.id_to_uuid.values())
        return [m for m in memos if m.uuid not in existing]

    def search(self, query_vec: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        vec = query_vec.reshape(1, -1).astype('float32')
        distances, indices = self.index.search(vec, top_k)
        return distances[0], indices[0]

    def rebuild(self, memos: List[Memo]) -> None:
        """
        全メモを読み直してインデックスを再構築。
        filter_new を使わず全量リビルドする際に呼び出す。
        """
        # 1) 空の IndexFlatL2 とマッピング初期化
        self.index = faiss.IndexFlatL2(self.dim)
        self.id_to_uuid.clear()

        # 2) 全メモの埋め込み行列をまとめて追加
        arr = np.stack([m.embedding for m in memos], axis=0).astype("float32")
        self.index.add(arr)

        # 3) 全件マッピングを 0..n-1 -> uuid
        for idx, memo in enumerate(memos):
            self.id_to_uuid[idx] = memo.uuid

        # 4) 永続化
        self.save()
