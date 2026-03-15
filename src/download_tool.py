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
        self.root.title("フォントをダウンロード中...")
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
    TEMP_ZIP1 = FONTS_DIR / "NotoSansCJKjp.zip"
    TEMP_ZIP2 = FONTS_DIR / "OpenMoji.zip"
    TEMP_ZIP3 = FONTS_DIR / "Jigmo.zip"

    # フォルダが存在しない場合は作成
    FONTS_DIR.mkdir(exist_ok=True)

    def download(url: str, dest: Path):
        if dest.exists():
            print(f"[SKIP] {dest.name} は既に存在します")
            return
        print(f"[GET] {dest.name} をダウンロード中...")
        urllib.request.urlretrieve(url, dest)

    print("=== フォントを準備中 ===")

    # --- フォント ---
    # NotoSansCJKjp (zip 展開)
    # https://github.com/notofonts/noto-cjk
    if not (FONTS_DIR / "NotoSansCJKjp-Medium.otf").exists():
        download("https://github.com/googlefonts/noto-cjk/releases/download/Sans2.004/06_NotoSansCJKjp.zip", TEMP_ZIP1)
        with zipfile.ZipFile(TEMP_ZIP1, 'r') as zp:
            for name in zp.namelist():
                if name.endswith("NotoSansCJKjp-Medium.otf"):
                    print("[UNZIP] NotoSansCJKjp-Medium.otf を抽出")
                    zp.extract(name, FONTS_DIR)
                    (FONTS_DIR / name).rename(FONTS_DIR / "NotoSansCJKjp-Medium.otf")
        print(f"[DEL] {TEMP_ZIP1.name} を削除")
        TEMP_ZIP1.unlink(missing_ok=True)
    else:
        print("[SKIP] NotoSansCJKjp-Medium.otf は既に存在します")

    # OpenMoji (zip 展開)
    # https://github.com/hfg-gmuend/openmoji
    if not (FONTS_DIR / "OpenMoji-black-glyf.ttf").exists():
        download("https://github.com/hfg-gmuend/openmoji/releases/download/16.0.0/openmoji-font.zip", TEMP_ZIP2)
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

    # Unifont (JP & Upper) (直接ダウンロード)
    # https://unifoundry.com/unifont/
    download(
        "https://unifoundry.com/pub/unifont/unifont-17.0.03/font-builds/unifont_jp-17.0.03.otf",
        FONTS_DIR / "unifont_jp-17.0.03.otf"
    )
    download(
        "https://unifoundry.com/pub/unifont/unifont-17.0.03/font-builds/unifont_upper-17.0.03.otf",
        FONTS_DIR / "unifont_upper-17.0.03.otf"
    )

    # Jigmo (zip 展開)
    # https://kamichikoichi.github.io/jigmo/
    if not (FONTS_DIR / "Jigmo.ttf").exists():
        download("https://kamichikoichi.github.io/jigmo/Jigmo-20250912.zip", TEMP_ZIP3)
        with zipfile.ZipFile(TEMP_ZIP3, 'r') as zp:
            for name in zp.namelist():
                if name.endswith("Jigmo.ttf"):
                    print("[UNZIP] Jigmo.ttf を抽出")
                    zp.extract(name, FONTS_DIR)
                    (FONTS_DIR / name).rename(FONTS_DIR / "Jigmo.ttf")
                if name.endswith("Jigmo2.ttf"):
                    print("[UNZIP] Jigmo2.ttf を抽出")
                    zp.extract(name, FONTS_DIR)
                    (FONTS_DIR / name).rename(FONTS_DIR / "Jigmo2.ttf")
                if name.endswith("Jigmo3.ttf"):
                    print("[UNZIP] Jigmo3.ttf を抽出")
                    zp.extract(name, FONTS_DIR)
                    (FONTS_DIR / name).rename(FONTS_DIR / "Jigmo3.ttf")
        TEMP_ZIP3.unlink(missing_ok=True)
    else:
        print("[SKIP] Jigmo.ttf は既に存在します")

    print("[完了] すべてのファイルが準備されました。")

# 実行
if __name__ == "__main__":
    gui = LogWindow()
    gui.start(main_task)
