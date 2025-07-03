# Dependency Analyzer ツール構成とファイル説明

以下は、Dependency Analyzer CLI プロジェクトのディレクトリ構成および各ファイルの役割・説明です。

```text
dependency_analyzer/           # パッケージルート
├── __init__.py                # パッケージ認識用（空ファイル）
├── main.py                    # CLI エントリポイント
├── config.py                  # スキャン除外ディレクトリ設定
├── mapper.py                  # Python ファイル検出＆モジュール名マッピング
├── analyzer.py                # AST による依存関係解析ロジック
└── formatter.py               # 出力フォーマット（DOT / テキスト）
```

## 実行方法：
```bash
# 解析したいディレクトリに移動
python3 -m dependency_analyzer.main .
```

---

## main.py

**役割**: コマンドラインインタフェースを定義し、ユーザーからのオプションを受け取って各モジュールを呼び出すエントリポイント。

* Click を利用して `root`／`--dot`／`--debug` オプションをパース
* `build_module_map` → `analyze_dependencies` → `output_*` の処理フローを制御
* ログレベル設定（通常／デバッグ）
* 実行時のエラーをキャッチして日本語メッセージで通知

---

## config.py

**役割**: スキャン時に除外すべきディレクトリ名を定義。

```python
VENDOR_DIRS = {'venv', '.venv', 'site-packages', '__pycache__'}
```

* `find_py_files` で `part in VENDOR_DIRS` をチェックし、仮想環境やキャッシュフォルダを対象外にする。

---

## mapper.py

**役割**: 指定ディレクトリ配下の `.py` ファイルを再帰検索し、ファイルパス→モジュール名マップを作成。

1. `find_py_files(root)`

  * `.rglob('*.py')` で Python ファイルを一覧
  * `VENDOR_DIRS` や `tests` ディレクトリ、`main.py`／`app.container.py` などのエントリポイントを除外
2. `build_module_map(root)`

  * 各ファイルパスから `root` 以下の相対パスを取得し `path.with_suffix('')`
  * `src/` ディレクトリ名を除外、`__init__.py` をパッケージ名扱い
  * 空文字列・`main`・`app.container` モジュールはスキップ
  * `{'interfaces.controllers.memo': Path(...), ...}` のようなマップを返却

---

## analyzer.py

**役割**: AST（抽象構文木）を使ってインポート文を解析し、内部モジュール間の依存エッジを抽出。

* モジュールのトップレベル名集合を作成し、標準ライブラリ／サードパーティを排除
* `ast.walk` で `Import`／`ImportFrom` ノードを検出
* `record_edge` で以下のみマッチング

  * **完全一致** (`import domain.memo`)
  * **子モジュール** (`import domain.memo.submodule` → 親 `domain.memo` に依存)
  * **親モジュール** (`import domain` → `domain.memo` などの子を検出)
* 不正な解析失敗は `WARNING` ログとして記録

---

## formatter.py

**役割**: 解析結果（依存エッジのリスト）をユーザー指定の形式で出力。

* **DOT 形式** (`output_dot`)：

  * `digraph dependencies { ... }` の Graphviz DOT ファイルを生成
  * `logger.info`／`debug`／`error` を日本語ログ
* **テキスト形式** (`output_text`)：

  * `src -> dst` の形で標準出力に一覧

---

以上のモジュールを組み合わせることで、

* **テストやツール、依存ライブラリは除外**し、
* **自分たちのソースファイル同士**の依存関係のみを正確に抽出・可視化

