from pathlib import Path
from typing import List
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="VEC_",
        frozen=False, # テストでの上書きを許可するため mutable に設定
    )

    # アプリ情報
    title: str = Field("Vectorization Memo API", description="アプリタイトル")
    version: str = Field("1.0.0", description="バージョン")
    description: str = Field(
        "メモ保存＋セマンティック検索＋管理用 API",
        description="OpenAPI ドキュメントに表示される説明",
    )

    # ─── メモ／インデックス保存先───
    memos_root: Path = Field(
        default=REPO_ROOT / "memos",
        description="リポジトリ直下に作成する memos ディレクトリ",
    )
    index_data_root: Path = Field(
        default=REPO_ROOT / ".index_data",
        description="リポジトリ直下に作成するインデックスフォルダ",
    )

    # 埋め込みモデル
    model_name: str = Field(
        "sentence-transformers/LaBSE",
        description="SentenceTransformer モデル名",
    )
    chunk_size: int = Field(
        300,
        ge=1,
        description="テキスト分割チャンクサイズ",
    )

    # CORS
    cors_origins: List[AnyHttpUrl] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="許可するオリジン一覧",
    )

settings = Settings()
