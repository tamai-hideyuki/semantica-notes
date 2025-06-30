## 実行方法
```bash
PYTHONPATH=./src pytest
```

## DI 設定が正確に動作していることをテスト
```bash
PYTHONPATH=./src pytest tests/unit/test_dependencies.py
```

## E2Eテスト
```bash
pytest \
  --maxfail=1 \
  --disable-warnings \
  -v \
  apps/backend/tests/integration
```

```text
apps/backend/tests/integration 内のテストだけを実行

--maxfail=1 で最初の失敗で中断

--disable-warnings で警告を抑制

-v で詳細情報を出力
```