from pathlib import Path
from .config import VENDOR_DIRS


def find_py_files(root: Path) -> list[Path]:
    """
    指定したディレクトリ以下を再帰的に検索し、
    VENDOR_DIRS に含まれるディレクトリをスキップして
    .py ファイルのリストを返す。"""
    files: list[Path] = []
    for path in root.rglob('*.py'):
        if any(part in VENDOR_DIRS for part in path.parts):
            continue
        files.append(path)
    return files
