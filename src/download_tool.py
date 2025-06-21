from pathlib import Path
import sys
import threading
import time
import shutil
import zipfile
import urllib.request

import tkinter as tk
from tkinter.scrolledtext import ScrolledText

# GUIウィンドウ定義
class LogWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("フォントとJISデータをダウンロード中...")
        self.root.geometry("600x400")

        self.text = ScrolledText(self.root, state='disabled', font=("Consolas", 10))
        self.text.pack(expand=True, fill="both")

        sys.stdout = self
        sys.stderr = self

    def write(self, msg):
        self.text.configure(state='normal')
        self.text.insert("end", msg)
        self.text.see("end")
        self.text.configure(state='disabled')
        self.text.update()

    def flush(self):
        pass

    def start(self, task):
        def wrapped_task():
            task()
            print("[INFO] 3秒後にウィンドウを閉じ、MiniCapturePrintを起動します...")
            time.sleep(3)
            self.root.quit()

        threading.Thread(target=wrapped_task, daemon=True).start()
        self.root.mainloop()

# 実処理
def main_task():
    BASE_DIR = Path(__file__).resolve().parent.parent
    FONTS_DIR = BASE_DIR / "fonts"
    DATA_DIR = BASE_DIR / "data"
    TEMP_ZIP1 = FONTS_DIR / "NotoSansJP.zip"
    TEMP_ZIP2 = FONTS_DIR / "OpenMoji.zip"

    # フォルダが存在しない場合は作成
    FONTS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    def download(url: str, dest: Path):
        if dest.exists():
            print(f"[SKIP] {dest.name} は既に存在します")
            return
        print(f"[GET] {dest.name} をダウンロード中...")
        urllib.request.urlretrieve(url, dest)

    print("=== フォントとJISデータを準備中 ===")

    # --- フォント ---
    # NotoSansJP (zip 展開)
    # https://github.com/notofonts/noto-cjk
    if not (FONTS_DIR / "NotoSansJP-Medium.otf").exists():
        download("https://github.com/notofonts/noto-cjk/releases/download/Sans2.004/16_NotoSansJP.zip", TEMP_ZIP1)
        with zipfile.ZipFile(TEMP_ZIP1, 'r') as zp:
            for name in zp.namelist():
                if name.endswith("NotoSansJP-Medium.otf"):
                    print("[UNZIP] NotoSansJP-Medium.otf を抽出")
                    zp.extract(name, FONTS_DIR)
                    (FONTS_DIR / name).rename(FONTS_DIR / "NotoSansJP-Medium.otf")
        print(f"[DEL] {TEMP_ZIP1.name} を削除")
        TEMP_ZIP1.unlink(missing_ok=True)
        print
    else:
        print("[SKIP] NotoSansJP-Medium.otf は既に存在します")

    # OpenMoji (zip 展開)
    # https://github.com/hfg-gmuend/openmoji
    if not (FONTS_DIR / "OpenMoji-black-glyf.ttf").exists():
        download("https://github.com/hfg-gmuend/openmoji/releases/download/15.1.0/openmoji-font.zip", TEMP_ZIP2)
        with zipfile.ZipFile(TEMP_ZIP2, 'r') as zp:
            for name in zp.namelist():
                if name.endswith("OpenMoji-black-glyf.ttf"):
                    print("[UNZIP] OpenMoji-black-glyf.ttf を抽出")
                    zp.extract(name, FONTS_DIR)
                    (FONTS_DIR / name).rename(FONTS_DIR / "OpenMoji-black-glyf.ttf")
                    subdir = FONTS_DIR / Path(name).parent
                    if subdir.exists() and subdir.is_dir():
                        shutil.rmtree(subdir)
        print(f"[DEL] {TEMP_ZIP2.name} を削除")
        TEMP_ZIP2.unlink(missing_ok=True)
    else:
        print("[SKIP] OpenMoji-black-glyf.ttf は既に存在します")

    # Unifont (JP)
    # https://unifoundry.com/unifont/
    download(
        "https://unifoundry.com/pub/unifont/unifont-16.0.03/font-builds/unifont_jp-16.0.03.otf",
        FONTS_DIR / "unifont_jp-16.0.03.otf"
    )

    # --- JISデータ ---
    # https://www.unicode.org/ + https://github.com/hatotank/WPT
    jis_files = {
        "JIS0201.TXT": "http://unicode.org/Public/MAPPINGS/OBSOLETE/EASTASIA/JIS/JIS0201.TXT",
        "JIS0208.TXT": "http://unicode.org/Public/MAPPINGS/OBSOLETE/EASTASIA/JIS/JIS0208.TXT",
        "JIS0212.TXT": "http://unicode.org/Public/MAPPINGS/OBSOLETE/EASTASIA/JIS/JIS0212.TXT",
        "JIS0213-2004.TXT": "https://raw.githubusercontent.com/hatotank/WPT/refs/heads/main/JIS0213-2004.TXT",
    }

    for filename, url in jis_files.items():
        download(url, DATA_DIR / filename)

    print("[完了] すべてのファイルが準備されました。")

# 実行
if __name__ == "__main__":
    gui = LogWindow()
    gui.start(main_task)
