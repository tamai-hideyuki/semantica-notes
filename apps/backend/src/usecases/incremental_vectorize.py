from typing import List, Tuple
from fastapi import FastAPI
import numpy as np
from anyio import to_thread

from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoRepository
from infrastructure.persistence.faiss_chunk_repo import FaissChunkRepository
from infrastructure.services.embedder import EmbedderService

class IncrementalVectorizeUseCase:
    def __init__(
        self,
        chunk_repo: FaissChunkRepository,
        memo_repo: MemoRepository,
        app: FastAPI,
        embedder: EmbedderService = EmbedderService(),
    ) -> None:
        self._chunk_repo = chunk_repo
        self._memo_repo  = memo_repo
        self._app        = app
        self._embedder   = embedder

        # 進捗 state の初期化
        self._app.state.vectorize_progress = {"processed": 0, "total": 0}

    async def execute(self) -> None:
        logger = getattr(self._app, "logger", None)
        if logger:
            logger.info("IncrementalVectorizeUseCase: START")
        else:
            print("UseCase START")

        # 1) 全メモ取得
        all_memos: List[Memo] = await self._memo_repo.list_all() or []
        # 2) 未ベクトル化分を抽出
        to_vectorize: List[Memo] = await self._chunk_repo.filter_new(all_memos) or []

        total = len(to_vectorize)
        # 進捗情報をまとめて更新
        self._app.state.vectorize_progress.update(total=total, processed=0)

        if total == 0:
            if logger:
                logger.info("No new memos to vectorize.")
            else:
                print("新規メモなし")
            return

        # 3) 各メモをチャンク→エンコード→追加
        for idx, memo in enumerate(to_vectorize, start=1):
            # encode_chunks は CPU バウンドの可能性があるため thread で実行
            chunked: List[Tuple[str, np.ndarray]] = await to_thread.run_sync(
                lambda text: self._embedder.encode_chunks(text),
                memo.body or memo.title or ""
            )

            # (chunk_id, vector) ペアをまとめて生成
            items: List[Tuple[str, np.ndarray]] = [
                (f"{memo.uuid}_{i}", vec)
                for i, (_, vec) in enumerate(chunked)
            ]

            # バッチ追加（実装側で一括追加に対応）
            self._chunk_repo.add_chunks_batch(items)

            # 進捗更新
            self._app.state.vectorize_progress["processed"] = idx

            if logger:
                logger.info(f"Vectorized memo {memo.uuid} ({idx}/{total})")
            else:
                print(f"ベクトル化完了: {memo.uuid} ({idx}/{total})")

        if logger:
            logger.info("All chunks added to FAISS index.")
            logger.info("IncrementalVectorizeUseCase: COMPLETE")
        else:
            print("FAISS への追加完了")
            print("UseCase COMPLETE")
