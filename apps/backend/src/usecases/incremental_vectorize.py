from typing import List
from fastapi import FastAPI
import numpy as np
from anyio import to_thread

from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoRepository
from interfaces.repositories.index_repo import IndexRepository

class IncrementalVectorizeUseCase:
    def __init__(
        self,
        index_repo: IndexRepository,
        memo_repo: MemoRepository,
        app: FastAPI,
    ):
        self._index_repo = index_repo
        self._memo_repo  = memo_repo
        self._app        = app

        # 進捗 state の初期化
        if not hasattr(app.state, "vectorize_progress"):
            app.state.vectorize_progress = {"processed": 0, "total": 0}

    async def execute(self) -> None:
        print("🧠 【UseCase】execute START")

        # 全メモ取得／未ベクトル化抽出
        all_memos    = await self._memo_repo.list_all()
        to_vectorize = await self._index_repo.filter_new(all_memos)
        total = len(to_vectorize)
        self._app.state.vectorize_progress.update(total=total, processed=0)
        print(f"📄 全メモ数={len(all_memos)}, 🆕 対象={total}")

        if total == 0:
            print("✅ 新規メモなし")
            return

        # モデルロード＋エンコードをスレッド実行 (プロセス化しない)
        def _encode(texts: List[str]):
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("sentence-transformers/LaBSE", device="cpu")
            print("🧩 モデルロード完了")
            return model.encode(
                texts,
                batch_size=32,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

        texts = [m.body or m.title or "" for m in to_vectorize]
        embeddings = await to_thread.run_sync(_encode, texts)

        # エンコード結果をMemoに貼り付け
        for memo, emb in zip(to_vectorize, embeddings):
            memo.embedding = np.asarray(emb, dtype="float32")

        # FAISS に一括追加＆保存
        self._index_repo.incremental_update(to_vectorize)
        print("💾 FAISS への追加完了")

        # 完了マーク
        self._app.state.vectorize_progress["processed"] = total
        print("✅ ベクトル化ユースケース完了")
