#!/usr/bin/env python3
"""
Dependency Analyzer CLI
指定した ROOT 以下のインポート依存を解析し、
標準出力または Graphviz DOT に出力するツール。
"""

import sys
import click
from pathlib import Path
import logging

from .mapper    import build_module_map
from .analyzer  import analyze_dependencies
from .formatter import output_dot, output_text

# ── ログ設定 ──
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(name)-25s %(levelname)-5s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("dep-analyzer")

def resolve_default_root(ctx, param, value):
    if value:
        return value
    return Path(__file__).parent.parent

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument(
    "root",
    required=False,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    callback=resolve_default_root,
)
@click.option(
    "--dot",
    "dotfile",
    type=click.Path(dir_okay=False, path_type=Path),
    help="依存関係を Graphviz DOT 形式で <file> に出力",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="デバッグログを有効化",
)
def main(root: Path, dotfile: Path, debug: bool):
    # debug モードなら全ログを DEBUG レベルに
    if debug:
        logger.setLevel(logging.DEBUG)
        for mod in (
            "dep-analyzer",
            "dependency_analyzer.mapper",
            "dependency_analyzer.analyzer",
            "dependency_analyzer.formatter",
        ):
            logging.getLogger(mod).setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    logger.info(f"Analyzing dependencies under: {root}")

    module_map = build_module_map(root)
    logger.debug(f"Found {len(module_map)} modules")

    edges = analyze_dependencies(module_map)
    logger.debug(f"Collected {len(edges)} dependency edges")

    if dotfile:
        output_dot(edges, dotfile)
        logger.info(f"Wrote graph to {dotfile}")
    else:
        output_text(edges)

if __name__ == "__main__":
    try:
        main(prog_name="dep-analyzer")
    except Exception:
        logger.exception("Fatal error during execution")
        sys.exit(1)
