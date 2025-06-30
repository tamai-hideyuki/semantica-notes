import pytest
from datetime import datetime
from domain.memo import Memo

def test_snippet_short_body():
    m = Memo(uuid="1", title="t", body="hello", category="c", tags=["a"], created_at=datetime.now())
    assert m.snippet == "hello"

def test_snippet_long_body():
    long_body = "x" * 120
    m = Memo(uuid="1", title="t", body=long_body, category="c", tags=["a"], created_at=datetime.now())
    assert m.snippet == "x" * 100 + "..."
