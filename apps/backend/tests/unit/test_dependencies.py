import pytest
from pathlib import Path
from datetime import datetime, timezone

import interfaces.controllers.common as common
from main import (
    _provide_memo_repo,
    _provide_index_repo,
    _provide_datetime_provider,
    app,
)
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from infrastructure.persistence.faiss_index_repo import FaissIndexRepository
from infrastructure.utils.datetime_jst import DateTimeJST
from config import settings


@pytest.fixture(autouse=True)
def reset_settings(tmp_path, monkeypatch):
    """
    settings.memos_root と settings.index_data_root をテスト用ディレクトリに差し替え。
    """
    monkeypatch.setattr(settings, "memos_root", str(tmp_path / "memos"))
    monkeypatch.setattr(settings, "index_data_root", str(tmp_path / "index"))
    return tmp_path

def test_provide_memo_repo_returns_filesystem_repo(tmp_path):
    repo = _provide_memo_repo()
    assert isinstance(repo, FileSystemMemoRepository)
    # root が settings.memos_root を指していること
    assert repo.root == Path(settings.memos_root)

def test_provide_index_repo_returns_faiss_repo(tmp_path):
    # まず memo_repo 用のインスタンスを作成
    memo_repo = _provide_memo_repo()
    index_repo = _provide_index_repo(memo_repo)
    assert isinstance(index_repo, FaissIndexRepository)
    # index_dir が settings.index_data_root
    assert index_repo.index_dir == Path(settings.index_data_root)
    # 内部に注入された memo_repo が同一オブジェクト
    assert index_repo.memo_repo is memo_repo

def test_provide_datetime_provider_returns_datetimejst():
    provider = _provide_datetime_provider()
    assert isinstance(provider, DateTimeJST)
    # now() が JST タイムゾーンの datetime を返す
    dt = provider.now()
    # UTC との差が +9時間であること
    offset = dt.utcoffset()
    assert offset is not None and offset.total_seconds() == 9 * 3600

def test_dependency_overrides_registered():
    """
    FastAPI の dependency_overrides に
    common.get_memo_repo, get_index_repo, get_datetime_provider
    が登録されていることを確認。
    """
    overrides = app.dependency_overrides
    assert common.get_memo_repo in overrides
    assert common.get_index_repo in overrides
    assert common.get_datetime_provider in overrides

