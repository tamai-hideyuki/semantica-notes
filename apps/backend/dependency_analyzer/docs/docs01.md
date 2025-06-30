```text
dependency_analyzer/                 ← パッケージルート
├── __init__.py                     # パッケージ認識用（空ファイル）
├── __main__.py                     # CLI エントリポイント／引数解析・ログ設定・全体制御
├── config.py                       # 除外ディレクトリ設定（VENDOR_DIRS）
├── scanner.py                      # ファイル探索ロジック（find_py_files）
├── mapper.py                       # モジュールマップ生成ロジック（build_module_map）
├── analyzer.py                     # AST 解析＆依存抽出ロジック（analyze_dependencies）
├── formatter.py                    # 出力ロジック（Graphviz DOT／テキスト）
└── analyzer_utils.py               # ※もし分離しているなら「除外判定ロジック」を担うユーティリティ
```

各ファイルの役割：

- **__main__.py**  
  - `click` を使った CLI 定義  
  - `--debug` フラグでログレベル切替  
  - `root`／`--dot` オプションの解析  
  - 各モジュール呼び出しによるワークフロー制御  
  - `logging.basicConfig` による全体ログフォーマット設定

- **config.py**  
  - 仮想環境や外部ライブラリディレクトリを定義する定数 `VENDOR_DIRS`

- **scanner.py**  
  - `find_py_files(root: Path) -> list[Path]`  
  - 指定ディレクトリ以下を再帰検索し、`VENDOR_DIRS` に含まれるパスを除外して `.py` ファイルを列挙

- **mapper.py**  
  - `build_module_map(root: Path) -> dict[str, Path]`  
  - `scanner.py` の結果を受け取り、ファイルパスをドット区切りのモジュール名にマッピング

- **analyzer.py**  
  - `analyze_dependencies(module_map) -> List[Edge]`  
  - AST をパースし、`import`／`from` 文から取得したモジュール名と `module_map` のキーをマッチング  
  - `Edge(src, dst)` のリストを構築

- **formatter.py**  
  - `output_dot(edges, dotfile)`：Graphviz DOT 形式でファイルへ出力  
  - `output_text(edges)`：標準出力へ `src -> dst` テキスト出力

- **analyzer_utils.py**（任意）  
  - `is_vendor_module(module_name: str) -> bool`  
  - `VENDOR_DIRS` を元に、解析対象外とすべきインポートを判定  

――以上の構成により、各責務が明確に分離され、保守性と拡張性を担保した設計。


## 実行方法:

```bash
python -m dependency_analyzer ./src --dot deps.dot --debug
```
