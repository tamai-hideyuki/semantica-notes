import logging
from typing import List
from pathlib import Path
from .analyzer import Edge

logger = logging.getLogger(__name__)

def output_dot(edges: List[Edge], dotfile: Path) -> None:
    """
    Graphviz DOT 形式で依存グラフを書き出す
    """
    logger.info(f"DOTファイルに依存エッジを出力します（件数: {len(edges)}）: {dotfile}")
    lines = ['digraph dependencies {']
    for e in edges:
        lines.append(f'    "{e.src}" -> "{e.dst}";')
    lines.append('}')
    try:
        dotfile.write_text("\n".join(lines), encoding='utf-8')
        logger.debug("DOTファイルの書き込みに成功しました")
    except Exception as e:
        logger.error(f"DOTファイルの書き込みに失敗しました: {dotfile} ({e})")

# テキスト形式で依存リストを標準出力

def output_text(edges: List[Edge]) -> None:
    """
    テキスト形式で依存リストを標準出力
    """
    logger.info(f"テキスト形式で依存エッジを出力します（件数: {len(edges)}）")
    for e in edges:
        print(f'{e.src} -> {e.dst}')
