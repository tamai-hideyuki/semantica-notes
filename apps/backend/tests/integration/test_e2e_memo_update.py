import os
import threading
import time
import pytest
from fastapi.testclient import TestClient
from pathlib import Path

# Import the FastAPI app
from src.main import app
from apps.backend.src.interfaces.controllers.memo_controller import _get_repo
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository

client = TestClient(app)

@pytest.fixture(autouse=True)
def temp_memo_dir(tmp_path, monkeypatch):
    # Create a temporary directory for memos
    memo_root = tmp_path / "memos"
    memo_root.mkdir()
    # Override the repository dependency to use the temp dir
    monkeypatch.setattr(
        "apps.backend.src.interfaces.controllers.memo_controller._get_repo",
        lambda: FileSystemMemoRepository(root=memo_root)
    )
    return memo_root

@pytest.fixture
def create_memo_file(temp_memo_dir):
    # Helper to create a memo file under category 'test'
    def _create(uuid: str, title: str, body: str):
        category_dir = temp_memo_dir / "test"
        category_dir.mkdir()
        file_path = category_dir / f"{uuid}.txt"
        content = f"UUID: {uuid}\nCREATED_AT: {time.strftime('%Y-%m-%dT%H:%M:%S')}\nTITLE: {title}\nTAGS:\nCATEGORY: test\nSCORE:0\n---\n{body}\n"
        file_path.write_text(content, encoding="utf-8")
        return uuid, file_path
    return _create

def test_lock_file_lifecycle(create_memo_file):
    uuid, file_path = create_memo_file("u1", "old", "old body")
    # Perform update
    response = client.put(f"/api/memo/{uuid}", json={"title": "new", "body": "new body"})
    assert response.status_code == 200
    # Lock file should not remain
    assert not os.path.exists(str(file_path) + ".lock")

def test_update_and_get_return_updated(create_memo_file):
    uuid, file_path = create_memo_file("u2", "t", "b")
    # Update
    update_res = client.put(f"/api/memo/{uuid}", json={"title": "t2", "body": "b2"})
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["title"] == "t2"
    assert data["body"] == "b2"
    # Get
    get_res = client.get(f"/api/memo/{uuid}")
    assert get_res.status_code == 200
    data2 = get_res.json()
    assert data2["title"] == "t2"
    assert data2["body"] == "b2"

def test_get_nonexistent_returns_404():
    res = client.get("/api/memo/not-exist")
    assert res.status_code == 404

def test_concurrent_updates(create_memo_file):
    uuid, file_path = create_memo_file("u3", "c1", "body1")
    errors = []
    def worker(title, body):
        try:
            r = client.put(f"/api/memo/{uuid}", json={"title": title, "body": body})
            if r.status_code != 200:
                errors.append(r.status_code)
        except Exception as e:
            errors.append(str(e))

    # Launch two concurrent updates
    t1 = threading.Thread(target=worker, args=("a", "1"))
    t2 = threading.Thread(target=worker, args=("b", "2"))
    t1.start(); t2.start()
    t1.join(); t2.join()
    # Ensure no errors
    assert not errors
    # Final file content should be one of the updates, and no corruption
    final = file_path.read_text(encoding="utf-8")
    assert "TITLE: a" in final or "TITLE: b" in final
    assert "..." not in final or '---' in final  # basic sanity
