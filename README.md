# Semantica Notes

> vectorization-memo をクリーンアーキテクチャ＋DDDで再構築した、ベクトル化パーソナルメモシステム。


## 概要

Semantica-Notis は、ドキュメントを「意味」で整理し、  
LaBSE 等のベクトル検索とシームレスに連携する管理プラットフォームです。

-  **意味単位の構造化**：トピック・要約・本文・タグで情報を明示的に区分
-  **高精度ベクトル検索**：キーワード一致を超えた文脈一致で「本当に欲しい情報」を提供
-  **Git & JSON/YAML対応**：バージョン管理・CI/CD・オフライン運用にも完全対応

>  どれほど優秀な検索エンジンでも、情報入力が曖昧では真価を発揮しません。  
> 「意味を見つけてもらいやすい文章を書くこと」が、Semantica-Notis の大前提です。

---


## 主な特徴

* 意味検索
  * Sentence-Transformers (LaBSE) による高品質ベクトル化
  * FAISS によるミリ秒単位近似最近傍検索
* クリーンアーキテクチャ（DDD）
  * Domain / UseCase / Interface / Infrastructure の明確なレイヤー分離
  * 依存性逆転の原則（Dependency Inversion Principle）を徹底
* リッチなメモモデル
  * `uuid`、`title`、`body`、`tags[]`、`category`、`created_at`、`score` などをサポート
  * 検索結果にスニペット表示機能
* 高性能・スケーラブル
  * 非同期 I/O とバルク処理で大量データに対応
  * Docker コンテナによる水平スケーリング
* セキュリティ
  * インターフェース層での入力バリデーション
  * レイヤーごとの明示的依存関係管理

### バックエンド

* API エンドポイント
  * `GET /api/memos` — 全メモ取得
  * `POST /api/memos` — メモ作成
  * `GET /api/memos/search?query=xxx&top_k=5` — 意味検索
* 検索処理
  1. LaBSE で埋め込みベクトルを生成
  2. FAISS で近傍ベクトルを検索
  3. UUID をキーにメモデータを取得

### フロントエンド

* メモ一覧表示
* メモ作成フォーム
* 意味検索（リアルタイムサジェスト付き）
* メモ詳細・編集
* 開発サーバー：`next dev -p 3000`

---

## インストール・起動方法

```bash
# リポジトリをクローン
git clone https://github.com/tamai-hideyuki/semantica-notes.git
cd semantica-notes

# Docker Compose で一括起動
docker-compose up -d
```

* バックエンド API: `http://localhost:8000`
* フロントエンド: `http://localhost:3000`

## 使い方

1. **メモ作成**

   ```bash
   curl -X POST http://localhost:8000/api/memos \
     -H "Content-Type: application/json" \
     -d '{"title":"例タイトル","body":"メモ本文","tags":["tag1","tag2"],"category":"カテゴリ"}'
   ```
2. **意味検索**

   ```bash
   curl "http://localhost:8000/api/memos/search?query=キーワード&top_k=5"
   ```
3. **UI 操作**

    * ブラウザでフロントエンドにアクセスし、直感的にメモの作成・検索が可能

---

```bash

# /-----------frontend-----------/
npm install         # まだなら依存インストール
npm run dev         # ポート 3000 


# /-----------backend-----------/

# 仮想環境の作成
python3 -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate

# 依存パッケージのインストール
pip install --upgrade pip
pip install -r requirements.txt

# アプリ起動
# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 「OSに優しい」運用
python run.py
```

## 依存関係確認
- [**バックエンドはこの .md で確認**](./apps/backend/dependency_analyzer/docs/docs01.md)


**フロントエンド**

```bash
# インストール
npm install --save-dev madge

# DOT 形式で出力
npx madge --extensions ts,tsx --image graph.svg src

# 依存サイクルの検出
npx madge --extensions ts,tsx --circular src
```

```text
--extensions ts,tsx で .ts/.tsx を対象に

--image で Graphviz 形式の画像を生成

--circular で循環依存をリストアップ
```
## Dependency Cruiser
Dependency Cruiser はもう少し細かいルール設定もできる依存関係チェッカーです。
```bash
# インストール
npm install --save-dev dependency-cruiser

# デフォルト設定ファイル生成
npx depcruise --init

# 依存グラフの出力 (JSON or DOT)
npx depcruise --ext .ts,.tsx src --output-type dot > graph.dot

# HTML レポート生成
npx depcruise --ext .ts,.tsx src --output-type html --output graph.html
```

```text
設定ファイルで「特定フォルダ／ファイルを無視」「レイヤー間の禁止依存をチェック」なども可能
アーキテクチャルルールの逸脱を自動検知
```