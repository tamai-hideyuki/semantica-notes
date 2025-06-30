from pydantic import BaseModel


class MemoUpdateDTO(BaseModel):
    """
    メモ更新用 DTO
    クライアントから受け取る更新データを定義
    """
    title: str  # メモのタイトル
    body: str   # メモの本文

    class Config:
        # BaseModel の設定: 未定義フィールドは無視
        extra = "ignore"
