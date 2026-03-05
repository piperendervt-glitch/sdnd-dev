"""低スペック向け軽量サンドボックス

subprocess + タイムアウト + 作業ディレクトリ分離で実現。
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

TIMEOUT_SEC = 30
WORK_DIR_BASE = Path(__file__).parent.parent / "sessions" / "sandbox_work"


class Sandbox:
    def __init__(self):
        self.work_dir: Path | None = None

    def __enter__(self):
        WORK_DIR_BASE.mkdir(parents=True, exist_ok=True)
        self.work_dir = Path(tempfile.mkdtemp(dir=WORK_DIR_BASE))
        return self

    def __exit__(self, *args):
        if self.work_dir and self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)

    def run_python(self, code: str) -> dict:
        """Pythonコードを隔離ディレクトリで実行"""
        script = self.work_dir / "script.py"
        script.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                ["python", "-X", "utf8", str(script)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=TIMEOUT_SEC,
                cwd=self.work_dir,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[:2000],
                "stderr": result.stderr[:1000],
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "stdout": "", "stderr": f"タイムアウト（{TIMEOUT_SEC}秒）"}

    def git_init(self) -> str:
        """作業ディレクトリをgit初期化"""
        subprocess.run(["git", "init"], cwd=self.work_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "sdnd@local"], cwd=self.work_dir, capture_output=True)
        subprocess.run(["git", "config", "user.name", "SDND-Dev"], cwd=self.work_dir, capture_output=True)
        return str(self.work_dir)

    def git_commit(self, message: str) -> dict:
        """変更をコミット"""
        subprocess.run(["git", "add", "."], cwd=self.work_dir, capture_output=True)
        result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=self.work_dir,
            capture_output=True,
            text=True,
        )
        return {"success": result.returncode == 0, "output": result.stdout}
