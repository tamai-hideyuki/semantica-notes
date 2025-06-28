import os
# PyTorch のマルチスレッド処理をシンプル化
os.environ["MKL_THREADING_LAYER"] = "GNU"
os.environ["OMP_NUM_THREADS"]     = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

import multiprocessing
multiprocessing.set_start_method("spawn", force=True)

from src.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, workers=1)
