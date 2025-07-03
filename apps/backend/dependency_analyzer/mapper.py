import logging
from pathlib import Path
from .config import VENDOR_DIRS

logger = logging.getLogger(__name__)

def find_py_files(root: Path) -> list[Path]:
    """
    指定ディレクトリ以下から .py ファイルを再帰的に検索し、
    VENDOR_DIRS、テストディレクトリ、エントリポイントファイルをスキップして
    Path リストを返却する
    """
    logger.info(f"検索対象ルートディレクトリ: {root} を走査しています")
    files: list[Path] = []
    for path in root.rglob('*.py'):
        # ベンダーディレクトリを除外
        if any(part in VENDOR_DIRS for part in path.parts):
            continue
        # テストディレクトリを除外
        if 'tests' in path.parts:
            continue
        # エントリポイントファイルを除外
        if path.name in ('main.py', 'app.container.py'):
            continue
        files.append(path)
    logger.debug(f"検出された Python ファイル数: {len(files)} 件")
    return files


def build_module_map(root: Path) -> dict[str, Path]:
    """
    モジュール名（パス区切りをドットに変換）→ ファイルパス のマップを構築

    - src ディレクトリはトップレベルとして扱い、モジュール名に含めない
    - __init__.py はパッケージモジュールとしてディレクトリ名のみを使用
    - ルート直下のエントリポイントモジュール(main, app.container)を除外
    """
    py_files = find_py_files(root)
    logger.info(f"Python ファイルからモジュールマップを構築します（ファイル数: {len(py_files)} 件）")
    module_map: dict[str, Path] = {}
    for path in py_files:
        # root 以下の相対パスを取得し、拡張子除去
        rel = path.relative_to(root).with_suffix('')
        parts = list(rel.parts)
        # src をトップレベルディレクトリとして除外
        if parts and parts[0] == 'src':
            parts = parts[1:]
        # __init__.py はパッケージ名として扱う（ファイル名を除外）
        if parts and parts[-1] == '__init__':
            parts = parts[:-1]
        # モジュール名を組み立て
        module = '.'.join(parts) if parts else ''
        # ルート直下のエントリポイントモジュールを除外
        if not module or module == 'main' or module.startswith('app.container'):
            continue
        module_map[module] = path
        logger.debug(f"モジュール登録: {module} -> {path}")
    logger.info(f"モジュールマップ完成（モジュール数: {len(module_map)} 件）")
    return module_map
