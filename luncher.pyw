# ランチャー
import subprocess
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent
src_dir = base_dir / "src"

# ダウンロードスクリプト
subprocess.run(
    [sys.executable, str(src_dir / "download_tool.py")]
)

# GUI本体
subprocess.Popen(
    [sys.executable, str(src_dir / "main.py")],
    cwd=base_dir,
    shell=True
)
