import logging
from typing import List
from pathlib import Path
from .analyzer import Edge

logger = logging.getLogger(__name__)

def output_dot(edges: List[Edge], dotfile: Path) -> None:
    """
    Graphviz DOT 形式で依存グラフを書き出す
    """
    logger.info(f"Writing {len(edges)} edges to DOT file: {dotfile}")
    logger.debug(f"Edges: {[(e.src, e.dst) for e in edges]}")
    lines = ['digraph dependencies {']
    for e in edges:
        lines.append(f'    "{e.src}" -> "{e.dst}";')
    lines.append('}')
    try:
        dotfile.write_text("\n".join(lines), encoding='utf-8')
        logger.debug("DOT file written successfully")
    except Exception as e:
        logger.error(f"Failed to write DOT file {dotfile}: {e}")


def output_text(edges: List[Edge]) -> None:
    """
    テキスト形式で依存リストを標準出力
    """
    logger.info(f"Outputting {len(edges)} edges to text")
    for e in edges:
        print(f'{e.src} -> {e.dst}')
