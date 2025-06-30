import logging
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from .config import VENDOR_DIRS

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class Edge:
    src: str
    dst: str


def analyze_dependencies(module_map: Dict[str, Path]) -> List[Edge]:
    """
    各ソースファイルの AST を解析し、import による依存エッジを抽出
    """
    logger.info(f"Starting analysis for {len(module_map)} modules")
    edges: List[Edge] = []
    for src, path in module_map.items():
        logger.debug(f"Processing module {src} at {path}")
        try:
            source = path.read_text(encoding='utf-8')
            tree = ast.parse(source)
        except Exception as e:
            logger.warning(f"Failed to parse {path}: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name
                    _record_edge(src, imported, module_map, edges)
            elif isinstance(node, ast.ImportFrom):
                # 相対インポート
                if node.level:
                    base = src.split('.')[:len(src.split('.')) - node.level]
                    for alias in node.names:
                        imported = '.'.join(base + [alias.name])
                        _record_edge(src, imported, module_map, edges)
                else:
                    imported = node.module or ''
                    _record_edge(src, imported, module_map, edges)

    logger.info(f"Analysis complete: found {len(edges)} dependency edges")
    return edges


def _record_edge(src: str, imported: str,
                 module_map: Dict[str, Path], edges: List[Edge]) -> None:
    """
    imported 名と module_map のキーをフレキシブルにマッチングして Edge を追加
    """
    # ベンダー/仮想環境モジュールの除外
    if not imported or imported in VENDOR_DIRS or any(imported.startswith(v + '.') for v in VENDOR_DIRS):
        logger.debug(f"Skipped vendor or empty import '{imported}' in {src}")
        return

    # モジュール名とインポート名のプレフィックス/サフィックスを許容
    for dst in module_map:
        if (imported == dst
            or imported.startswith(f"{dst}.")
            or dst.startswith(f"{imported}.")
            or imported.endswith(f".{dst}")
            or dst.endswith(f".{imported}")):
            logger.debug(f"Matched import '{imported}' to module '{dst}'")
            edges.append(Edge(src, dst))
