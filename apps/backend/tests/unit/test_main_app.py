import pytest
from pathlib import Path
from datetime import timedelta, datetime, timezone

from fastapi.testclient import TestClient

import interfaces.controllers.common as common
from main import create_app, app
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from infrastructure.persistence.faiss_index_repo import FaissIndexRepository
from infrastructure.utils.datetime_jst import DateTimeJST
from interfaces.utils.datetime import DateTimeProvider
from config import settings

@pytest.fixture(autouse=True)
def reset_settings(tmp_path, monkeypatch):
    """
    settings のパスを一時ディレクトリに差し替える
    """
    monkeypatch.setattr(settings, "memos_root", tmp_path / "memos")
    monkeypatch.setattr(settings, "index_data_root", tmp_path / "index")
    return tmp_path

@pytest.mark.parametrize("fixture_app", [create_app(), app])
def test_dependency_overrides_registered(fixture_app):
    overrides = fixture_app.dependency_overrides

    # 抽象プロバイダがキーになっている
    assert common.get_memo_repo in overrides
    assert common.get_index_repo in overrides
    assert common.get_datetime_provider in overrides

    # 値として正しい具象クラスのインスタンスが返るか
    memo_repo = overrides[common.get_memo_repo]()
    assert isinstance(memo_repo, FileSystemMemoRepository)
    assert memo_repo.root == Path(settings.memos_root)

    index_repo = overrides[common.get_index_repo](memo_repo)
    assert isinstance(index_repo, FaissIndexRepository)
    assert index_repo.memo_repo is memo_repo
    assert index_repo.index_dir == Path(settings.index_data_root)

    dt_provider = overrides[common.get_datetime_provider]()
    assert isinstance(dt_provider, DateTimeJST)
    now = dt_provider.now()
    # JST は UTC+9h であること
    offset = now.utcoffset()
    assert offset == timedelta(hours=9)

def test_app_routes_exist():
    client = TestClient(app)
    # /api/search が登録されているか
    resp = client.post("/api/search", json={"query": ""})
    # 422 か 200 のどちらか
    assert resp.status_code in (200, 422)
