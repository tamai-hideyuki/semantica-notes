import logging
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set

from .config import VENDOR_DIRS

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Edge:
    src: str
    dst: str

    """

    各ソースファイルの AST を解析し、import による依存エッジを抽出
    （標準／サードパーティは除外し、完全一致 or 親子関係のみをマッチ）
    """

def analyze_dependencies(module_map: Dict[str, Path]) -> List[Edge]:
    logger.info(f"解析対象モジュール数: {len(module_map)} 件")
    # トップレベルモジュール名の集合（標準＋サードパーティを弾くため）
    top_levels: Set[str] = {name.split('.')[0] for name in module_map.keys()}

    edges: List[Edge] = []
    for src, path in module_map.items():
        logger.debug(f"モジュール解析中: {src} ({path})")
        try:
            source = path.read_text(encoding='utf-8')
            tree = ast.parse(source)
        except Exception as e:
            logger.warning(f"解析に失敗しました: {path} ({e})")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    record_edge(src, alias.name, module_map, edges, top_levels)
            elif isinstance(node, ast.ImportFrom):
                # 相対インポート解決
                if node.level and node.module:
                    parts = src.split('.')
                    base = parts[:len(parts) - node.level]
                    imported = '.'.join(base + [node.module])
                else:
                    imported = node.module or ''
                record_edge(src, imported, module_map, edges, top_levels)

    logger.info(f"解析完了: 依存エッジ数 {len(edges)} 件")
    return edges


def record_edge(
    src: str,
    imported: str,
    module_map: Dict[str, Path],
    edges: List[Edge],
    top_levels: Set[str],
) -> None:
    root = imported.split('.')[0]
    # プロジェクト外（標準ライブラリ／pip）を除外
    if root not in top_levels or root in VENDOR_DIRS:
        logger.debug(f"外部インポートをスキップ: '{imported}' in {src}")
        return

    # 完全一致 or 親子関係のみ
    for dst in module_map:
        if imported == dst:
            edges.append(Edge(src, dst))
            logger.debug(f"[完全一致] {src} -> {dst}")
            return
        if imported.startswith(f"{dst}."):
            edges.append(Edge(src, dst))
            logger.debug(f"[子モジュール] {src} -> {dst}")
            return
        if dst.startswith(f"{imported}."):
            edges.append(Edge(src, dst))
            logger.debug(f"[親モジュール] {src} -> {dst}")
            return
