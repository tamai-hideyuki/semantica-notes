import logging
from pathlib import Path
from .config import VENDOR_DIRS

logger = logging.getLogger(__name__)


def find_py_files(root: Path) -> list[Path]:
    """
    指定ディレクトリ以下から .py ファイルを再帰的に検索し、
    VENDOR_DIRS に含まれるディレクトリをスキップして Path リストを返却
    """
    logger.info(f"Scanning for Python files under root: {root}")
    files = [path for path in root.rglob('*.py')
             if not any(part in VENDOR_DIRS for part in path.parts)]
    logger.debug(f"Total files found: {len(files)}")
    for path in files:
        logger.debug(f"Found file: {path}")
    return files


def build_module_map(root: Path) -> dict[str, Path]:
    """
    モジュール名（パス区切りをドットに変換）→ ファイルパス のマップを構築
    """
    py_files = find_py_files(root)
    logger.info(f"Building module map from {len(py_files)} files")
    module_map: dict[str, Path] = {}
    for path in py_files:
        rel = path.relative_to(root).with_suffix('')
        module = '.'.join(rel.parts)
        module_map[module] = path
        logger.debug(f"Mapping module: {module} -> {path}")
    logger.info(f"Module map constructed with {len(module_map)} entries")
    logger.debug(f"Module map keys: {list(module_map.keys())}")
    return module_map
