import os
import time
import fcntl


class FileLock:
    """
    fcntl を使ってファイル単位の排他ロックを実現するユーティリティクラス
    使用例:
        with FileLock(path_to_target_file):
            # ファイル操作を安全に実行
    """
    def __init__(self, target_path: str, timeout: float = 10.0, delay: float = 0.1):
        # 対象ファイルのパス
        self.target_path = target_path
        # ロック用ファイル (.lock) のパス
        self.lock_path = f"{target_path}.lock"
        # ロック取得のタイムアウト（秒）
        self.timeout = timeout
        # ロック再試行の間隔（秒）
        self.delay = delay
        self._fd = None

    def acquire(self):
        """
        ロックの取得を試みる。タイムアウトまで待機し、取得できなければ例外を送出。
        """
        start_time = time.time()
        # ロック用ファイルを開く（存在しなければ作成）
        self._fd = open(self.lock_path, 'w')
        while True:
            try:
                # 排他 (Exclusive) かつ 非ブロッキングでロックを試行
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                # ロック取得成功
                break
            except BlockingIOError:
                # タイムアウト判定
                if (time.time() - start_time) >= self.timeout:
                    raise TimeoutError(
                        f"{self.target_path} のロックが {self.timeout} 秒以内に取得できませんでした。"
                    )
                # 指定間隔だけ待機して再試行
                time.sleep(self.delay)

    def release(self):
        """
        ロックを解除し、ロックファイルを削除する。
        """
        if self._fd:
            try:
                # ロック解除
                fcntl.flock(self._fd.fileno(), fcntl.LOCK_UN)
            except IOError:
                pass
            # ファイルディスクリプタをクローズ
            self._fd.close()
            # ロックファイルを削除
            try:
                os.remove(self.lock_path)
            except FileNotFoundError:
                pass

    def __enter__(self):
        # with 文の開始時にロックを取得
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # with 文の終了時にロックを解放
        self.release()
