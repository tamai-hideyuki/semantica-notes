from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """
    アプリケーションの各種設定を管理するクラス。
    .env ファイルおよび VEC_ プレフィックス付き環境変数から読み込みます。
    """
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="VEC_",
        frozen=False,
    )

    # ── アプリケーション情報 ──
    title: str = Field(
        "Vectorization Memo API",
        description="アプリタイトル"
    )
    version: str = Field(
        "1.0.0",
        description="バージョン"
    )
    description: str = Field(
        "メモ保存＋セマンティック検索＋管理用 API",
        description="OpenAPI ドキュメントに表示される説明"
    )

    # ── ディレクトリ設定 ──
    memos_root: Path = Field(
        default=REPO_ROOT / "memos",
        description="メモファイルを格納するディレクトリ"
    )
    index_data_root: Path = Field(
        default=REPO_ROOT / ".index_data",
        description="索引用データを格納するディレクトリ"
    )

    # ── モデル／検索設定 ──
    model_name: str = Field(
        "sentence-transformers/LaBSE",
        description="SentenceTransformer モデル名"
    )
    chunk_size: int = Field(
        300,
        ge=1,
        description="テキスト分割チャンクサイズ"
    )
    embedding_dim: int = Field(
        768,
        ge=1,
        description="埋め込みモデルの次元数"
    )

    # ── ハイブリッド検索の重み設定 ──
    hybrid_semantic_weight: float = Field(
        0.6,
        ge=0.0, le=1.0,
        description="ハイブリッド検索でのセマンティックスコアの重み"
    )
    hybrid_elastic_weight: float = Field(
        0.4,
        ge=0.0, le=1.0,
        description="ハイブリッド検索での全文検索スコアの重み"
    )

    faiss_index_path: Path = Field(
        default=REPO_ROOT / ".index_data" / "chunks.index",
        description="FAISS チャンク索引用インデックスファイルパス"
    )

    # ── CORS 設定 ──
    cors_origins: List[AnyHttpUrl] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="許可するオリジン一覧"
    )

    # ── Elasticsearch 設定 ──
    # 文字列 or JSON 配列 or リストをそのまま受け取り、
    # get_elastic_repo() で正規化します
    elasticsearch_hosts: Union[str, List[AnyHttpUrl]] = Field(
        "http://localhost:9200",
        description="Elasticsearch のホスト URL 一覧 (カンマ区切り文字列 or JSON 配列)",
        env="ELASTICSEARCH_HOSTS",
    )
    elasticsearch_index: str = Field(
        "memos",
        description="Elasticsearch のインデックス名",
        env="ELASTICSEARCH_INDEX"
    )

# グローバル設定オブジェクト
settings = Settings()
