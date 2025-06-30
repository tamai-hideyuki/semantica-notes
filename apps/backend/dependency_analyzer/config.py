from pathlib import Path

# 動的に除外したいディレクトリプレフィックス
VENDOR_DIRS: set[str] = {'venv', '.venv', 'site-packages', '__pycache__'}
