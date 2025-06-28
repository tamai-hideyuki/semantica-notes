import ast
import os
import argparse
from pathlib import Path

# 動的に除外したいディレクトリプレフィックス
VENDOR_DIRS = {'venv', '.venv', 'site-packages', '__pycache__'}


def find_py_files(root: Path):
    """
    .py ファイルを再帰的に検索し、
    VENDOR_DIRS を含むパスはスキップする
    """
    for path in root.rglob('*.py'):
        if any(part in VENDOR_DIRS for part in path.parts):
            continue
        yield path


class DependencyAnalyzer:
    """
    AST を使ってコードベース内の import 依存を解析
    """
    def __init__(self, root: Path):
        self.root = root
        self.module_map = self._build_module_map()

    def _build_module_map(self):
        """
        モジュール名 -> ファイルパス のマップを作成
        """
        module_map = {}
        for path in find_py_files(self.root):
            rel = path.relative_to(self.root).with_suffix('')
            module = '.'.join(rel.parts)
            module_map[module] = path
        return module_map

    def analyze(self):
        """
        コードベース内の依存を (src, dst) のタプルリストで返す
        """
        edges = []
        for src_module, path in self.module_map.items():
            try:
                tree = ast.parse(path.read_text(encoding='utf-8'))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self._record_edge(src_module, alias.name, edges)
                elif isinstance(node, ast.ImportFrom):
                    name = node.module or ''
                    self._record_edge(src_module, name, edges)
        return edges

    def _record_edge(self, src: str, imported: str, edges: list):
        """
        imported が module_map に登録されているか、そのサブモジュールであればエッジ追加
        """
        # 仮想環境や外部ライブラリのトップレベルを除外
        if any(imported.startswith(v + '.') or imported == v for v in VENDOR_DIRS):
            return

        for dst in self.module_map:
            if imported == dst or dst.startswith(imported + '.'):
                edges.append((src, dst))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Analyze Python import dependencies in a codebase.'
    )
    parser.add_argument('root', type=Path, help='Root directory to scan')
    parser.add_argument('--dot', type=Path, help='Output Graphviz DOT file')
    args = parser.parse_args()

    analyzer = DependencyAnalyzer(args.root)
    edges = analyzer.analyze()

    if args.dot:
        with open(args.dot, 'w', encoding='utf-8') as f:
            f.write('digraph dependencies {\n')
            for src, dst in edges:
                f.write(f'    "{src}" -> "{dst}";\n')
            f.write('}\n')
        print(f'Wrote graph to {args.dot}')
    else:
        for src, dst in edges:
            print(f'{src} -> {dst}')
