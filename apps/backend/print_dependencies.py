#!/usr/bin/env python3
"""
print_dependencies.py

このスクリプトは `backend/src` 配下のすべての Python ファイルを走査し、
インポートに基づく依存関係を CLI 出力します。

配置場所: `backend/print_dependencies.py`
使い方:
    cd backend
    python3 print_dependencies.py [root_dir]

root_dir を指定しない場合はスクリプトと同じディレクトリの `src` を対象とします。
"""

import os
import ast
import sys

def module_name_from_path(path: str, root: str) -> str:
    rel = os.path.relpath(path, root)
    mod_path = os.path.splitext(rel)[0]
    # ディレクトリ区切りをドットに変換
    return mod_path.replace(os.path.sep, ".")

def main():
    # 対象ディレクトリの取得
    if len(sys.argv) > 1:
        root = sys.argv[1]
    else:
        here = os.path.dirname(__file__)
        root = os.path.join(here, "src")

    edges = set()

    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                content = open(path, "r", encoding="utf-8").read()
                tree = ast.parse(content, filename=path)
            except Exception as e:
                print(f"WARNING: Failed to parse {path}: {e}", file=sys.stderr)
                continue

            mod_name = module_name_from_path(path, root)
            for node in ast.walk(tree):
                # 通常の import 文
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        edges.add(f"{mod_name} -> {alias.name}")
                # from ... import 文
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        edges.add(f"{mod_name} -> {node.module}")

    # ソートして出力
    for edge in sorted(edges):
        print(edge)

if __name__ == "__main__":
    main()
