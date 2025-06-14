from functools import lru_cache
from pathlib import Path
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import Tk, Label, Text, Button, Entry, Scrollbar, Frame, Canvas, Toplevel, Radiobutton, IntVar, StringVar, Checkbutton, BooleanVar, Scale, LabelFrame, TclError, font, simpledialog, HORIZONTAL, messagebox
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw, ImageTk, ImageGrab, ImageEnhance, ImageOps, ImageFilter

import re
import sys
import threading
import queue
import keyboard
import os
import numpy as np
import inspect
import unicodedata
import ctypes

from config import ConfigHandler # config.pyからのインポート
from printer import PrinterHandler # printer.pyからのインポート
from ui_settings import SettingsWindow # ui_settings.pyからのインポート

# 定数
PRINTER_IMAGE_MAX_WIDTH = 512
PRINTER_IMAGE_MAX_HEIGHT = 960

BARCODE_TAGS = {
    "QR":    {"pattern": r"<QR:(.+?)>",    "tag": "qr_tag",   "bg": "#e8fce8", "fg": "#006600"},
    "ITF":   {"pattern": r"<ITF:(.+?)>",   "tag": "itf_tag",  "bg": "#f4e8ff", "fg": "#6a1b9a"},
    "EAN13": {"pattern": r"<EAN13:(.+?)>", "tag": "ean_tag",  "bg": "#eeeeee", "fg": "#222222"},
    "C39":   {"pattern": r"<C39:(.+?)>",   "tag": "c39_tag",  "bg": "#e7f0fa", "fg": "#004488"},
    "B128":  {"pattern": r"<B128:(.+?)>",  "tag": "b128_tag", "bg": "#fff3e0", "fg": "#a63d00"},
}

# 色付け用タグ（配置用タグとは分離）
CUSTOM_TAGS = {
    "HR": {"pattern": r"<HR>", "tag": "hr_tag", "bg": "#E0E0E0", "fg": "#757575"},
    "ALIGN_CENTER_COLOR": {"pattern": r"<ALIGN:CENTER>", "tag": "align_center_color", "bg": "#90CAF9", "fg": "#1976D2"},
    "ALIGN_LEFT_COLOR":   {"pattern": r"<ALIGN:LEFT>",   "tag": "align_left_color",   "bg": "#A5D6A7", "fg": "#388E3C"},
    "ALIGN_RIGHT_COLOR":  {"pattern": r"<ALIGN:RIGHT>",  "tag": "align_right_color",  "bg": "#FFE0B2", "fg": "#BF360C"},
}

# タグのグループ化
STYLE_TAG_GROUPS = {
    "size": ["bold", "four", "vert"],
    "decoration": ["underline", "invert"]
}

# Bayer マトリックスを生成
@lru_cache(maxsize=4)
def bayer_matrix(n):
    """
    Bayer マトリックスを生成

    :param int n: マトリクスのサイズ（2, 4, 8 のいずれか）
    :return: Bayer マトリックス
    :rtype: numpy.ndarray
    :raises ValueError: 未対応のサイズの場合
    """
    if n == 1:
        return np.array([[0]])
    else:
        smaller_matrix = bayer_matrix(n // 2)
        return np.block([
            [4 * smaller_matrix, 4 * smaller_matrix + 2],
            [4 * smaller_matrix + 3, 4 * smaller_matrix + 1]
        ]) / (n * n)


# random マトリックスを生成
@lru_cache(maxsize=100)
def random_matrix(n, seed=0):
    """
    random マトリックスを生成

    :param int n: マトリクスのサイズ（2, 4, 8 のいずれか）
    :param int seed: 乱数シード値
    :return: 正規化されたランダムマトリックス
    :rtype: numpy.ndarray
    """
    np.random.seed(seed)  # 再現性のためにシードを固定
    matrix = np.random.rand(n, n)
    flat = matrix.flatten()
    ranks = flat.argsort().argsort()  # ランク化（0〜n^2-1）
    normalized = ranks.reshape((n, n)) / (n * n)
    return normalized


# clusterd マトリックスを生成
@lru_cache(maxsize=4)
def clustered_matrix(n):
    """
    クラスターマトリックスを生成

    :param int n: マトリクスのサイズ（2, 4, 8 のいずれか）
    :return: クラスターマトリックス
    :rtype: numpy.ndarray
    :raises ValueError: 未対応のサイズの場合（2, 4, 8 のみ対応）
    """
    # 4x4クラスタマトリクス（Ulichney の方式ベース）
    base_4x4 = np.array([
        [12,  5,  6, 13],
        [ 4,  0,  1,  7],
        [11,  3,  2,  8],
        [15, 10,  9, 14]
    ]) / 16.0

    # 8x8クラスタマトリクス（Ulichney の方式ベース）
    base_8x8 = np.array([
        [36, 16, 28, 48, 37, 17, 29, 49],
        [12,  0,  4, 20, 13,  1,  5, 21],
        [44, 24, 32, 52, 45, 25, 33, 53],
        [ 8,  2,  6, 22,  9,  3,  7, 23],
        [40, 18, 30, 50, 41, 19, 31, 51],
        [14, 10,  6, 26, 15, 11,  7, 27],
        [46, 26, 34, 54, 47, 27, 35, 55],
        [10,  6,  8, 24, 11,  7,  9, 25]
    ]) / 64.0

    if n == 4:
        return base_4x4
    elif n == 8:
        return base_8x8
    elif n == 2:
        return np.array([[0, 2], [3, 1]]) / 4.0
    else:
        raise ValueError("clustered_matrix: 未対応のサイズです（2, 4, 8 のみ対応）")


class InptDialog(simpledialog.Dialog):
    """
    入力ダイアログボックスを表示するクラス。
    """
    def __init__(self, parent, title=None, prompt="入力してください:"):
        """
        ダイアログの初期化

        :param parent: 親ウィジェット
        :param str title: ダイアログのタイトル
        :param str prompt: 入力を促すプロンプトメッセージ
        """
        self.prompt = prompt
        super().__init__(parent, title)

    def body(self, master):
        """
        ダイアログの本体を作成

        :param master: 親ウィジェット
        :return: Entryウィジェット
        :rtype: Entry
        """
        win = self.winfo_toplevel()
        win.resizable(False, False)  # サイズ変更を無効化
        win.geometry("350x120")  # ウィンドウサイズを指定
        self.resizable(False, False)  # サイズ変更を無効化

        Label(master, text=self.prompt).pack(pady=(10, 0))
        self.entry = Entry(master, width="40")
        self.entry.pack(pady=(5, 10))
        return self.entry

    def apply(self):
        """
        OKボタン押下時の処理。入力値をself.resultに格納。
        """
        self.result = self.entry.get()

    def buttonbox(self):
        """
        OK / キャンセルボタンの日本語化
        """
        box = Frame(self)
        w = Button(box, text="OK", width=10, command=self.ok, default="active")
        w.pack(side="left", padx=5, pady=5)
        w = Button(box, text="キャンセル", width=10, command=self.cancel)
        w.pack(side="left", padx=5, pady=5)

        self.bind("<Return>", self.ok)  # EnterキーでOKボタンを押す
        self.bind("<Escape>", self.cancel)  # Escキーでキャンセルボタンを押す
        box.pack()


class App(TkinterDnD.Tk):
    """
    メインアプリケーションクラス
    """
    def __init__(self, printer_image_max_width=PRINTER_IMAGE_MAX_WIDTH, printer_image_max_height=PRINTER_IMAGE_MAX_HEIGHT):
        """
        アプリケーションの初期化

        :param int printer_image_max_width: プリンタ画像の最大幅
        :param int printer_image_max_height: プリンタ画像の最大高さ
        """
        super().__init__() # TkinterDnD.Tk の初期化
        self.printer_image_max_width = printer_image_max_width
        self.printer_image_max_height = printer_image_max_height
        self.preview_window = None # プレビューウィンドウの参照を保持
        self.original_image = None
        self.processed_image = None
        self.icon = None
        self.dither_mode = IntVar(value=1) # ディザリング(1)、２値化(2)、ハイブリッド(3)
        self.widthforce_mode = BooleanVar(value=True) # 横幅固定の有効/無効
        self.rotate_load_enabled = BooleanVar(value=False) # 読込時90°回転の有効/無効
        self.auto_enlarge_enabled = BooleanVar(value=False) # 小さい画像を拡大の有効/無効
        self.alpha_channel_enabled = BooleanVar(value=True) # アルファチャンネルを白で合成の有効/無効
        self.contrast_enabled = BooleanVar(value=False) # コントラスト強調の有効/無効
        self.image_invert_enabled = BooleanVar(value=False) # 反転の有効/無効
        self.paper_cut_enabled = BooleanVar(value=True) # 用紙カットの有効/無効
        self.image_out_enabled = BooleanVar(value=True) # 画像印刷の有効/無効
        self.text_out_enabled = BooleanVar(value=True) # テキスト印刷の有効/無効
        self._is_handling_modified = False  # テキストウィジェットの変更を処理中かどうか

        self.filter_map = {
            "FIND_EDGES": ImageFilter.FIND_EDGES,
            "EDGE_ENHANCE": ImageFilter.EDGE_ENHANCE,
            "EDGE_ENHANCE_MORE": ImageFilter.EDGE_ENHANCE_MORE,
            "CONTOUR": ImageFilter.CONTOUR,
            "EMBOSS": ImageFilter.EMBOSS,
            #"SHARPEN": ImageFilter.SHARPEN,
            #"SMOOTH": ImageFilter.SMOOTH,
            "SMOOTH_MORE": ImageFilter.SMOOTH_MORE,
            "DETAIL": ImageFilter.DETAIL,
            "BLUR": ImageFilter.BLUR,
            #"GaussianBlur": ImageFilter.GaussianBlur,
            #"UnsharpMask": ImageFilter.UnsharpMask,
            #"GaussianBlur": ImageFilter.GaussianBlur,
            #"BoxBlur": ImageFilter.BoxBlur,
            #"MedianFilter": ImageFilter.MedianFilter,
        }
        # ハイブリッドディザリングの設定
        self.hybrid_dither_type = IntVar(value=0)   # 0=bayer, 1=random, 2=clustered
        self.hybrid_matrix_size = IntVar(value=4)   # 2, 4, 8
        self.hybrid_filter_enabled = IntVar(value=1) # 0=無効, 1=有効
        self.hybrid_filter_type = StringVar(value="FIND_EDGES")   # FIND_EDGES, EMBOSS, SMOOTH_MORE, EDGE_ENHANCE, EDGE_ENHANCE_MORE, DETAIL, CONTOUR
        self.hybrid_random_seed = IntVar(value=0)  # 0〜255のシード値

        # 設定を読み込む(設定はアプリ再起動後に反映)
        self.src_dir = Path(__file__).parent.resolve()  # srcディレクトリのパスを取得
        self.config_manager = ConfigHandler(self.src_dir / "../config/config.json")
        self.config = self.config_manager.load_config()

        # メインスレッドで処理を渡すためのキュー
        self.queue = queue.Queue()
        # キューを定期的にチェック
        self.check_queue()

        # タイトル設定
        self.title("MiniCapturePrint")
        # ウィンドウサイズ設定
        self.geometry("1050x720")
        # ウィンドウのリサイズを禁止
        self.resizable(False, False)

        # TM88IVクラス用設定
        self.tm88iv_config = {
            "jis0201_file": self.src_dir / "../data/JIS0201.TXT",  # JIS0201 データファイル
            "jis0208_file": self.src_dir / "../data/JIS0208.TXT",  # JIS0208 データファイル
            "jis0212_file": self.src_dir / "../data/JIS0212.TXT",  # JIS0212 データファイル
            "jis0213_file": self.src_dir / "../data/JIS0213-2004.TXT",  # JIS0213-2004 データファイル
            "emoji_font_file": self.src_dir / "../fonts/OpenMoji-black-glyf.ttf",  # 絵文字フォント
            "kanji_font_file": self.src_dir / "../fonts/NotoSansJP-Medium.otf",  # 日本語フォント
            "fallback_font_file": self.src_dir / "../fonts/unifont_jp-16.0.03.otf",  # フォールバックフォント
            # TM88IVクラスの引数ではないけど、ファイルチェックの関係上含める
            "icon_file": self.src_dir / "minicaptureprint.ico"  # アイコンファイル
        }

        # 絵文字フォント変更有効化している場合は、設定からフォントファイルを取得して設定
        emoji_font_enabled = self.config.get("printer_emoji_font_enabled", False)
        if emoji_font_enabled:
            self.tm88iv_config["emoji_font_file"] = self.src_dir / "../fonts" / self.config.get("printer_emoji_font","OpenMoji-black-glyf.ttf")

        # 必要なファイルが存在するかチェック
        for key, path in self.tm88iv_config.items():
            if not os.path.exists(path):
                self.show_error(f"必要なファイルが見つかりません: {path}", "ファイルエラー")
                sys.exit(1)  # アプリケーションを終了

        # 絵文字の残りの設定を追加
        if emoji_font_enabled:
            self.tm88iv_config["emoji_font_size"] = self.config.get("printer_emoji_font_size", 20)  # 絵文字フォントサイズ
            self.tm88iv_config["emoji_font_adjust_x"] = self.config.get("printer_emoji_font_adjust_x",0) # 絵文字フォントのX座標調整
            self.tm88iv_config["emoji_font_adjust_y"] = self.config.get("printer_emoji_font_adjust_y",0) # 絵文字フォントのX座標調整

        # グローバルホットキーの設定
        enable_hotkey = self.config.get("hotkey_enabled", True)
        # ホットキーが有効な場合は設定
        if enable_hotkey:
            self.setup_hotkey()
        # スタートアップモードを取得
        self.startup_mode = self.config.get("startup_mode", "form")  # デフォルトはフォーム表示
        # モード判定
        if self.startup_mode == "tray":
            self.withdraw()  # タスクトレイの場合はウィンドウを非表示にする
        # アイコンの設定
        myappid = 'net.hatotank.minicaptureprint' # アプリケーションIDを設定（Windowsのタスクトレイアイコン用）
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        ico_path = os.path.abspath(self.src_dir / "minicaptureprint.ico")
        self.iconbitmap(default=ico_path)  # アイコンを設定（.icoファイルを使用）

        # 最小化イベントをバインド
        self.bind("<Unmap>", self.on_minimize)
        # 閉じるボタンのイベントをバインド
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.boldfont = ("Yu Gothic UI", 12, "bold")
        self.base_font = font.Font(family="MS Gothic", size=13)
        self.bold_font = font.Font(family="MS Gothic", size=13, weight="bold")
        self.italic_font = font.Font(family="MS Gothic", size=13, slant="italic")
        self.four_font = font.Font(family="MS Gothic", size=20)  # ４倍角用フォント

        # フォームとボタンを追加
        self.create_form()


    def show_error(self, message, title="エラー"):
        """
        エラーメッセージを表示(共通ユーティリティ)

        :param str message: エラーメッセージ
        :param str title: ダイアログタイトル
        """
        func = inspect.currentframe().f_back.f_code.co_name
        messagebox.showerror(title, f"関数: {func}\n{message}")


    def setup_hotkey(self):
        """
        グローバルホットキーを設定
        """
        try:
            # ホットキーの組み合わせを取得
            hotkey_combination = self.config.get("hotkey_combination", "ctrl+alt+shift+c")
            # ホットキーを登録
            keyboard.add_hotkey(hotkey_combination, self.enqueue_capture_mode)
        except Exception as e:
            self.show_error(f"ホットキーの登録中にエラーが発生しました:\n{e}")


    def enqueue_capture_mode(self):
        """
        画面キャプチャモードをキューに追加
        """
        self.queue.put(self.start_rectangle_selection)


    def check_queue(self):
        """
        キューをチェックして処理を実行
        """
        try:
            while not self.queue.empty():
                func = self.queue.get_nowait()
                func()  # キューから取り出した関数を実行
        except queue.Empty:
            pass
        self.after(200, self.check_queue)  # 200msごとにキューをチェック


    def create_form(self):
        """
        メインフォームを作成
        """
        # 左側のデザイン
        # ボタン
        # 1列目
        Button(self, text="横倍角", command=lambda: self.toggle_tag("bold")).place(x=10, y=10, width=100, height=26)
        Button(self, text="４倍角", command=lambda: self.toggle_tag("four")).place(x=110, y=10, width=100, height=26)
        Button(self, text="アンダーライン", command=lambda: self.toggle_tag("underline")).place(x=210, y=10, width=100, height=26)
        Button(self, text="反転", command=lambda: self.toggle_tag("invert")).place(x=310, y=10, width=100, height=26)
        Button(self, text="縦倍角", command=lambda: self.toggle_tag("vert")).place(x=410, y=10, width=100, height=26)
        # 2列目
        Button(self, text="QR挿入", command=self.input_qr_barcode).place(x=10, y=40, width=100, height=26)
        Button(self, text="ITFコード挿入", command=self.input_itf_barcode).place(x=110, y=40, width=100, height=26)
        Button(self, text="EAN13挿入", command=self.input_ean13_barcode).place(x=210, y=40, width=100, height=26)
        Button(self, text="Code39挿入", command=self.input_code39_barcode).place(x=310, y=40, width=100, height=26)
        Button(self, text="Code128挿入", command=self.input_code128_barcode).place(x=410, y=40, width=100, height=26)
        # 3列目
        Button(self, text="水平線挿入", command=self.insert_horizontal_rule).place(x=10, y=70, width=100, height=26)
        Button(self, text="左寄せ", command=self.insert_align_left).place(x=210, y=70, width=100, height=26)
        Button(self, text="中央寄せ", command=self.insert_align_center).place(x=310, y=70, width=100, height=26)
        Button(self, text="右寄せ", command=self.insert_align_right).place(x=410, y=70, width=100, height=26)


        # テキスト入力フィールドとスクロールバーを含むフレームを作成
        text_frame = Frame(self, width=498, height=512, highlightthickness=2, highlightbackground="black")
        text_frame.place(x=11, y=140)
        # キャンバス
        self.line_info_canvas = Canvas(text_frame, width=64, bg="#f4f4f4", highlightthickness=0)
        self.line_info_canvas.place(x=0, y=0, width=64, height=506)
        # テキスト入力フィールド
        self.text_widget = Text(text_frame, wrap="char", font=self.base_font)
        self.text_widget.place(x=64, y=0, width=390, height=506)
        # スクロールバーを追加
        scrollbar = Scrollbar(text_frame, command=self.text_widget.yview)
        scrollbar.place(x=472, y=0, width=20, height=506)
        # スクロールバーをテキスト入力フィールドに関連付け
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        self.text_widget.bind("<KeyRelease>", lambda e: self.redraw_line_info())  # キーリリースイベントで行番号を更新
        self.text_widget.bind("ButtonRelease-1", lambda e: self.redraw_line_info()) # マウスボタンが離されたときも行番号を更新
        self.text_widget.bind("<MouseWheel>", lambda e: self.after(50, self.redraw_line_info()))  # マウスホイールでスクロールしたときも行番号を更新
        self.text_widget.bind("<Configure>", lambda e: self.redraw_line_info())  # テキストウィジェットのサイズ変更時に行番号を更新

        # 右側のデザイン
        # ラベルフレームを作成
        options_frame = LabelFrame(self, text="キャプチャ＆ファイル読込")
        options_frame.place(x=522, y=6, width=210, height=125)
        # ラベルフレーム：チェックボックス：横幅固定
        text_force_size = "横幅" + str(self.printer_image_max_width) + "固定"
        self.checkbutton3 = Checkbutton(options_frame, text=text_force_size, variable=self.widthforce_mode)
        self.checkbutton3.place(x=10, y=10, width=86, height=16)
        # ラベルフレーム：チェックボックス：読込時回転
        self.checkbutton4 = Checkbutton(options_frame, text="読込時90°回転", variable=self.rotate_load_enabled)
        self.checkbutton4.place(x=10, y=34, width=96, height=16)
        # ラベルフレーム：チェックボックス：小さい画像を拡大
        self.checkbutton5 = Checkbutton(options_frame, text="小さい画像を拡大", variable=self.auto_enlarge_enabled)
        self.checkbutton5.place(x=10, y=60, width=106, height=16)
        # アルファチャンネルを白で合成
        self.checkbutton8 = Checkbutton(options_frame, text="アルファチャンネルを白で合成", variable=self.alpha_channel_enabled)
        self.checkbutton8.place(x=10, y=84, width=154, height=16)
        # キャプチャボタン
        Button(options_frame, text="画面\nキャプチャ", command=self.start_rectangle_selection).place(x=122, y=10, width=80, height=46)

        # ラベルフレームを作成
        options_frame2 = LabelFrame(self, text="画像調節")
        options_frame2.place(x=740, y=6, width=292, height=125)
        # ラベルフレーム：ラジオボタン（ディザ、２値化）
        # ディザ
        self.radiobutton1 = Radiobutton(options_frame2, text="ディザ", variable=self.dither_mode, value=1, command=lambda: [self.update_preview(), self.update_hybrid_button_state()])
        self.radiobutton1.place(x=4, y=9)
        # ２値化
        self.radiobutton2 = Radiobutton(options_frame2, text="2値化", variable=self.dither_mode, value=2, command=lambda: [self.update_preview(), self.update_hybrid_button_state()])
        self.radiobutton2.place(x=64, y=9)
        # ラベルフレーム：ハイブリッド
        self.radiobutton3 = Radiobutton(options_frame2, text="ハイブリッド", variable=self.dither_mode, value=3, command=lambda: [self.update_preview(), self.update_hybrid_button_state()])
        self.radiobutton3.place(x=124, y=9)
        # ラベルフレーム：スライダー（濃さ調整）
        self.brightness_slider = Scale(options_frame2, from_=0.0, to=2.0, resolution=0.1, orient=HORIZONTAL)
        self.brightness_slider.set(1.0)  # 初期値を設定
        self.brightness_slider.config(command=lambda e: self.update_preview())
        self.brightness_slider.place(x=4, y=28, width=198, height=42)

        # ラベルフレーム：チェックボックス（コントラスト強調）
        self.checkbutton1 = Checkbutton(options_frame2, text="コントラスト強調", variable=self.contrast_enabled, command=self.update_preview)
        self.checkbutton1.place(x=4, y=84, width=102, height=18)
        # ラベルフレーム：チェックボックス（反転）
        self.checkbutton2 = Checkbutton(options_frame2, text="反転", variable=self.image_invert_enabled, command=self.update_preview)
        self.checkbutton2.place(x=124, y=84, width=60, height=18)
        self.hybrid_button = Button(options_frame2, text="ハイブリッド\n詳細設定", command=self.open_hybrid_settings)
        self.hybrid_button.place(x=204, y=10, width=80, height=46)

        # ピクチャボックス（画像表示用）
        self.picture_canvas = Canvas(self, width=512, height=512, bg="white", highlightthickness=2, highlightbackground="black")
        self.picture_canvas.place(x=520, y=140, width=512, height=512)
        # ピクチャボックスにドラッグ＆ドロップのイベントをバインド
        self.picture_canvas.drop_target_register(DND_FILES)
        self.picture_canvas.dnd_bind('<<Drop>>', self.on_drop)

        # 下側のデザイン
        # 設定ボタン
        Button(self, text="設定", command=self.open_settings).place(x=10, y=663, width=47, height=46)
        # デバッグボタン
        Button(self, text="デバッグ", command=lambda: self.debug_print_text_with_tags(self.text_widget)).place(x=60, y=663, width=47, height=46)

        # テキスト印刷
        self.checkbutton7 = Checkbutton(self, text="テキスト印刷", variable=self.text_out_enabled, command=self.update_preview)
        self.checkbutton7.place(x=680, y=666, width=84, height=16)
        # 画像印刷
        self.checkbutton6 = Checkbutton(self, text="画像印刷", variable=self.image_out_enabled, command=self.update_preview)
        self.checkbutton6.place(x=780, y=666, width=78, height=16)
        # 用紙カット
        self.checkbutton1 = Checkbutton(self, text="用紙カット", variable=self.paper_cut_enabled, command=self.update_preview)
        self.checkbutton1.place(x=780, y=692, width=80, height=16)
        # 印字ボタン
        Button(self, text="印刷", font=self.boldfont, command=self.print).place(x=886, y=663, width=147, height=46)

        # タグ定義
        # バーコードタグの設定
        for bc in BARCODE_TAGS.values():
            self.text_widget.tag_config(bc["tag"], background=bc["bg"], foreground=bc["fg"])
        # カスタムタグの設定
        for ct in CUSTOM_TAGS.values():
            self.text_widget.tag_config(ct["tag"], background=ct["bg"], foreground=ct["fg"])
        # 整形用タグの設定
        self.text_widget.tag_configure("bold", font=self.bold_font)
        self.text_widget.tag_configure("underline", underline=1)
        self.text_widget.tag_configure("invert", foreground="white", background="black")
        self.text_widget.tag_configure("four", font=self.four_font)  # ４倍角用フォント
        self.text_widget.tag_configure("vert", font=self.italic_font)

        self.text_widget.bind("<<Modified>>", self._on_text_modified)  # テキスト変更イベントをバインド

        # 初期状態の更新
        self.update_hybrid_button_state()


    def toggle_tag(self, tag_name):
        """
        指定されたタグをトグルする
        """
        try:
            start = self.text_widget.index("sel.first")
            end = self.text_widget.index("sel.last")
        except TclError:
            return
        tag_category = None
        for category, tags in STYLE_TAG_GROUPS.items():
            if tag_name in tags:
                tag_category = category
                break

        index = start
        all_have_tag = True
        while self.text_widget.compare(index, "<", end):
            if tag_name not in self.text_widget.tag_names(index):
                all_have_tag = False
                break
            index = self.text_widget.index(f"{index} +1c")

        if tag_category:
            for other_tag in STYLE_TAG_GROUPS[tag_category]:
                self.text_widget.tag_remove(other_tag, start, end)  # 他のスタイルタグを削除

        if all_have_tag:
            self.text_widget.tag_remove(tag_name, start, end)
        else:
            self.text_widget.tag_add(tag_name, start, end)


    def debug_print_text_with_tags(self, text_widget):
        """
        テキストウィジェットの内容とタグ状態をデバッグ出力

        :param text_widget: 対象のテキストウィジェット
        """
        total_lines = int(text_widget.index("end-1c").split(".")[0])
        print("=" * 40)
        print("Text Widget 内容とタグ状態（デバッグ出力）")
        for lineno in range(1, total_lines + 1):
            line_start = f"{lineno}.0"
            line_end = f"{lineno}.end"
            line_text = text_widget.get(line_start, line_end)
            tags_on_line = []

            for tag in text_widget.tag_names():
                ranges = text_widget.tag_ranges(tag)
                for i in range(0, len(ranges), 2):
                    rng_start = ranges[i]
                    rng_end = ranges[i + 1]
                    if text_widget.compare(rng_start, "<", line_end) and text_widget.compare(rng_end, ">", line_start):
                        tags_on_line.append(tag)
                        break  # 1つでも一致したらそのタグはリストに入れる

            print(f"{lineno:>3}: '{line_text}'  tags: {', '.join(tags_on_line) if tags_on_line else 'なし'}")
        print("=" * 40)


    def get_visual_width(self, s):
        """
        文字列の可視幅を計算する

        :param s: 対象の文字列
        :return: 可視幅（全角文字は2、半角文字は1として計算）
        """
        width = 0
        for ch in s:
            ea = unicodedata.east_asian_width(ch)
            width += 2 if ea in ('W', 'F', 'A') else 1
        return width


    def redraw_line_info(self):
        """
        テキストウィジェットの行番号を更新
        """
        self.line_info_canvas.delete("all")
        i = self.text_widget.index("@0,0") # 表示開始行
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:  # 行が存在しない場合は終了
                break
            y = dline[1]  # 行のY座標を取得
            line_num = str(i).split(".")[0]  # 行番号を取得
            line_text = self.text_widget.get(f"{line_num}.0", f"{line_num}.end")  # 行のテキストを取得
            vis_width = self.get_visual_width(line_text)  # 可視幅を計算

            # 警告色条件
            bg_color = "#f4f4f4" if vis_width <= (21 * 2) else "#ffeeba"  # フォントA(12×24)=42桁、漢字フォント(24×24)=21桁以内は通常色、それ以上は警告色(TM-T88IV基準)
            self.line_info_canvas.create_rectangle(0, y, 64, y + 17, fill=bg_color, outline="")
            self.line_info_canvas.create_text(4, y+2, anchor="nw", text=f"{line_num:>2}",font=("Consolas", 9))
            self.line_info_canvas.create_text(32, y+2, anchor="nw", text=f"{vis_width:>2}", font=("Consolas", 9))
            i = self.text_widget.index(f"{i}+1line") # 次の行へ移動


    def _on_text_modified(self, event):
        """
        テキストウィジェットの内容が変更されたときに呼び出されるイベントハンドラ

        :param event: イベントオブジェクト
        :type event: Event
        """
        if self._is_handling_modified:
            return
        self._is_handling_modified = True

        widget = event.widget
        if widget.edit_modified():
            self.text_widget.edit_modified(False)
            #print("テキストウィジェットの内容が変更されました。-----")
            self.reapply_alignment_tags()

        self._is_handling_modified = False


    def update_hybrid_button_state(self):
        """
        ハイブリッドモード選択時だけ詳細設定ボタンを有効化
        """
        # ディザリングモードがハイブリッドでない場合は無効化
        if self.dither_mode.get() == 3:
            self.hybrid_button.config(state="normal")
        else:
            self.hybrid_button.config(state="disabled")


    def open_settings(self):
        """
        設定ウィンドウを開く
        """
        SettingsWindow(self, self.config_manager)


    def open_hybrid_settings(self):
        """
        ハイブリッドディザリングの詳細設定ウィンドウを開く
        """
        if hasattr(self, 'hybrid_settings_window') and self.hybrid_settings_window.winfo_exists():
            # 既にウィンドウが存在する場合はフォーカスを当てる
            self.hybrid_settings_window.deiconify()  # ウィンドウを表示
            self.hybrid_settings_window.lift()  # ウィンドウを最前面に
            self.hybrid_settings_window.focus_force() # フォーカスを当てる
            return

        self.hybrid_settings_window = Toplevel(self)
        top = self.hybrid_settings_window
        top.title("ハイブリッド詳細設定")
        top.geometry("360x390")
        top.resizable(False, False)
        top.attributes("-topmost", True)  # 最前面
        top.protocol("WM_DELETE_WINDOW", lambda: [self.hybrid_settings_window.withdraw(), self.update_filter_state()])

        self.filter_radio_buttons = []  # フィルタのラジオボタンのリスト

        # === ラベルフレーム1：ディザタイプ＋マトリクス ===
        frame1 = LabelFrame(top, text="ディザ＆マトリクス")
        frame1.place(x=10, y=10, width=342, height=155)
        Label(frame1, text="ディザ種類").place(x=5, y=5)
        Radiobutton(frame1, text="bayer", value=0, variable=self.hybrid_dither_type, command=lambda: [self.update_preview(), self.update_random_seed()]).place(x=10, y=30)
        Radiobutton(frame1, text="clustered", value=2, variable=self.hybrid_dither_type, command=lambda: [self.update_preview(), self.update_random_seed()]).place(x=90, y=30)
        Radiobutton(frame1, text="random (ランダムマトリクス）", value=1, variable=self.hybrid_dither_type, command=lambda: [self.update_preview(), self.update_random_seed()]).place(x=10, y=55)
        Label(frame1, text="ランダムマトリクス用シード値").place(x=190, y=5)
        self.scale_random_seed = Scale(frame1, from_=0, to=99, orient=HORIZONTAL, variable=self.hybrid_random_seed, command=lambda e: self.update_preview())
        self.scale_random_seed.place(x=190, y=37, width=140)

        Label(frame1, text="マトリクス数").place(x=5, y=80)
        Radiobutton(frame1, text="2", value=2, variable=self.hybrid_matrix_size, command=self.update_preview).place(x=10, y=105)
        Radiobutton(frame1, text="4", value=4, variable=self.hybrid_matrix_size, command=self.update_preview).place(x=90, y=105)
        Radiobutton(frame1, text="8", value=8, variable=self.hybrid_matrix_size, command=self.update_preview).place(x=170, y=105)

        # === ラベルフレーム2：フィルタ ===
        frame2 = LabelFrame(top, text="フィルタ関係")
        frame2.place(x=10, y=175, width=342, height=180)

        Label(frame2, text="フィルタ適用（適用しないはディザ処理のみとなります）").place(x=5, y=5)
        Radiobutton(frame2, text="適用する", value=1, variable=self.hybrid_filter_enabled, command=lambda: [self.update_preview(), self.update_filter_state()]).place(x=10, y=30)
        Radiobutton(frame2, text="適用しない", value=0, variable=self.hybrid_filter_enabled, command=lambda: [self.update_preview(), self.update_filter_state()]).place(x=120, y=30)
        
        Label(frame2, text="フィルタ種類").place(x=5, y=55)
        rb_fe = Radiobutton(frame2, text="FIND_EDGES", value="FIND_EDGES", variable=self.hybrid_filter_type, command=self.update_preview)
        rb_fe.place(x=10, y=80)
        self.filter_radio_buttons.append(rb_fe)
        rb_ct = Radiobutton(frame2, text="CONTOUR", value="CONTOUR", variable=self.hybrid_filter_type, command=self.update_preview)
        rb_ct.place(x=120, y=80)
        self.filter_radio_buttons.append(rb_ct)
        rb_dt = Radiobutton(frame2, text="DETAIL", value="DETAIL", variable=self.hybrid_filter_type, command=self.update_preview)
        rb_dt.place(x=230, y=80)
        self.filter_radio_buttons.append(rb_dt)

        rb_eb = Radiobutton(frame2, text="EMBOSS", value="EMBOSS", variable=self.hybrid_filter_type, command=self.update_preview)
        rb_eb.place(x=10, y=105)
        self.filter_radio_buttons.append(rb_eb)
        rb_sm = Radiobutton(frame2, text="SMOOTH_MORE", value="SMOOTH_MORE", variable=self.hybrid_filter_type, command=self.update_preview)
        rb_sm.place(x=120, y=105)
        self.filter_radio_buttons.append(rb_sm)
        
        rb_en = Radiobutton(frame2, text="EDGE_ENHANCE", value="EDGE_ENHANCE", variable=self.hybrid_filter_type, command=self.update_preview)
        rb_en.place(x=10, y=130)
        self.filter_radio_buttons.append(rb_en)
        rb_em = Radiobutton(frame2, text="EDGE_ENHANCE_MORE", value="EDGE_ENHANCE_MORE", variable=self.hybrid_filter_type, command=self.update_preview)
        rb_em.place(x=120, y=130)
        self.filter_radio_buttons.append(rb_em)

        # 閉じる
        Button(top, text="閉じる", command=top.destroy).place(x=140, y=359, width=80, height=26)

        # 初期状態の更新
        self.update_random_seed()
        self.update_filter_state()


    def update_random_seed(self):
        """
        ランダムマトリクスのシード値用スケール状態の更新
        """
        value = self.hybrid_dither_type.get()
        enable = value == 1  # random マトリクスの場合のみ有効
        if enable:
            self.scale_random_seed.config(
                state="normal",
                troughcolor="#d9d9d9",  # スライダーのトラフの色を変更
                sliderrelief="raised",
                sliderlength=15
                )
        else:
            self.scale_random_seed.config(
                state="disabled",
                troughcolor="#eeeeee",  # 少し薄く
                sliderrelief="flat",
                sliderlength=10
                )
  

    def update_filter_state(self):
        """
        フィルタのラジオボタンの状態を更新
        """
        enabled = self.hybrid_filter_enabled.get() == 1
        for rb in self.filter_radio_buttons:
            rb.config(state="normal" if enabled else "disabled")


    def hybrid_dithering(self, image, edge_threshold=128, dither_type=0, matrix_size=4, filter_type="FIND_EDGES", filter_enabled=True, random_seed=0):
        """
        ハイブリッドディザリングを適用

        :param image: 入力画像（Pillow Image オブジェクト）
        :param edge_threshold: 2値化のしきい値
        :param matrix_size: マトリックスのサイズ
        :return: ハイブリッドディザリング後の画像
        """
        # matrix_size確認
        if matrix_size & (matrix_size - 1) != 0:
            current_function = inspect.currentframe().f_code.co_name
            messagebox.showerror("エラー", f"関数: {current_function}\nmatrix_sizeは2のべき乗で無ければいけない")
            return

        # グレースケールに変換
        image = image.convert("L")
        width, height = image.size
        
        if filter_enabled:
            # フィルタの設定を取得
            config_edge_detection = self.filter_map.get(filter_type, ImageFilter.FIND_EDGES)
            # フィルタを適用
            edges = image.filter(config_edge_detection)
            edge_pixels = np.array(edges, dtype=np.uint8)
            edge_pixels = (edge_pixels - edge_pixels.min()) / (np.ptp(edge_pixels) + 1e-5) * 255
        else:
            edge_pixels = np.full((height, width), edge_threshold)  # 全体を同一値に設定

        if dither_type == 0:
            # Bayer マトリックスを生成
            matrix = bayer_matrix(matrix_size) * 255 # 0-255 の範囲にスケール
        if dither_type == 1:
            # random マトリックスを生成
            matrix = random_matrix(matrix_size, random_seed) * 255
        elif dither_type == 2:
            # clustered マトリクスを生成
            matrix = clustered_matrix(matrix_size) * 255

        matrix = np.tile(matrix, (height // matrix_size + 1, width // matrix_size + 1))
        matrix = matrix[:height, :width]

        # ピクセルデータを取得
        pixels = np.array(image)

        # ハイブリッドディザリングを適用
        result = np.zeros_like(pixels, dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                if edge_pixels[y, x] > edge_threshold or filter_enabled == False:  # エッジ部分
                    result[y, x] = 255 if pixels[y, x] > matrix[y, x] else 0
                else:  # 無地部分
                    result[y, x] = 255 if pixels[y, x] > edge_threshold else 0

        # 新しい画像を作成
        return Image.fromarray(result, mode="L")


    def update_preview(self, image=None):
        """
        ラジオボタン、スライダー、チェックボックスの値に基づいて画像を更新します。
        """
        try:
            # オリジナル画像がない場合は何もしない
            if self.original_image is None:
                return

            # 新しい画像を読み込む場合は座標を初期化
            if image is not None:
                current_x, current_y = 0, 0
            else:
                current_coords = self.picture_canvas.coords(self.image_id) if hasattr(self, 'image_id') else [0, 0]
                current_x, current_y = current_coords if len(current_coords) == 2 else (0, 0)

            # 引数の画像がNoneの場合はオリジナル画像を使用
            if image is None:
                image = self.original_image.copy()

            # RGBAモードの場合はRGBに変換
            if image.mode == "RGBA":
                if self.alpha_channel_enabled.get():
                    background = Image.new("RGB", image.size, (255, 255, 255))  # 白背景
                    background.paste(image, mask=image.split()[-1])
                    image = background
                image = image.convert("RGB")

            # 画像の幅と高さを取得
            width, height = image.size

            # 幅がプリンタ画像最大値未満、以上の場合は最大値に拡大
            if (self.auto_enlarge_enabled.get() and width < self.printer_image_max_width) or width > self.printer_image_max_width: 
                # プリンタの画像最大幅をセット
                new_width = self.printer_image_max_width
                # アスペクト比を計算
                aspect_ratio = height / width
                # 高さをアスペクト比に基づいて計算
                new_height = int(new_width * aspect_ratio)
                # 画像をリサイズ
                image = image.resize((new_width, new_height), Image.LANCZOS)

            # コントラスト強調
            if self.contrast_enabled.get():
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)
            
            # 反転
            if self.image_invert_enabled.get():
                image = ImageOps.invert(image)

            # 明るさ調整
            image = ImageEnhance.Brightness(image).enhance(self.brightness_slider.get())

            # ディザリング
            if self.dither_mode.get() == 1:  
                image = image.convert("1")
            # 2値化
            elif self.dither_mode.get() == 2:
                image = image.convert("L")
                image = image.point(lambda x: 255 if x > 128 else 0, mode='1')
            # ハイブリッドディザリング
            elif self.dither_mode.get() == 3:
                image = self.hybrid_dithering(image,
                                              dither_type=self.hybrid_dither_type.get(),
                                              matrix_size=self.hybrid_matrix_size.get(),
                                              filter_type=self.hybrid_filter_type.get(),
                                              filter_enabled=self.hybrid_filter_enabled.get() == 1,
                                              random_seed=self.hybrid_random_seed.get())

            # 処理後の画像を保持
            self.processed_image = image

            # Tkinterで表示可能な形式に変換
            image_tk = ImageTk.PhotoImage(self.processed_image)

            # Canvasをクリアして新しい画像を表示
            self.picture_canvas.delete("all")
            self.image_id = self.picture_canvas.create_image(current_x, current_y, anchor="nw", image=image_tk)
            self.image_tk = image_tk  # 参照を保持
            self.picture_canvas.config(scrollregion=self.picture_canvas.bbox(self.image_id))

            # ドラッグ＆ドロップを有効化
            self.enable_image_drag()

        except Exception as e:
            self.show_error(f"画像の更新中にエラーが発生しました:\n{e}")
            return


    def start_rectangle_selection(self):
        """
        矩形選択モードを開始します。
        """
        # ウィンドウを非表示にする
        self.withdraw()

        self.selection_window = Toplevel(self)
        self.selection_window.attributes("-fullscreen", True)
        self.selection_window.attributes("-alpha", 0.3)  # 半透明
        self.selection_window.attributes("-topmost", True)  # 常に最前面に表示
        self.selection_window.focus_force()  # フォーカスを強制的に当てる
        self.selection_window.configure(bg="gray")

        self.canvas = Canvas(self.selection_window, cursor="cross", bg="gray")
        self.canvas.pack(fill="both", expand=True)

        # マウスイベントをバインド
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)  # 左クリックで矩形選択開始
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)  # マウスをドラッグして矩形を描画
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)  # 左クリックを離したときに矩形選択を確定
        self.canvas.bind("<ButtonPress-3>", self.cancel_rectangle_selection)  # 右クリックでキャンセル
 

    def cancel_rectangle_selection(self, event=None):
        """
        矩形選択モードをキャンセルします。
        """
        if self.selection_window:
            self.selection_window.destroy()
            self.selection_window = None

        # ウィンドウを再表示する
        self.deiconify()


    def on_mouse_press(self, event):
        """
        マウスの左ボタンが押されたときの処理。
        """
        self.start_x = event.x
        self.start_y = event.y
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline="#FF1493", width=3 # ディープピンク
        )


    def on_mouse_drag(self, event):
        """
        マウスをドラッグしている間の処理。
        """
        if self.rect_id:
            # 現在の幅を計算
            current_width = abs(event.x - self.start_x)

            # 横幅強制モードが有効な場合
            x2 = event.x
            if self.widthforce_mode.get():
                # 横幅が超える場合
                if current_width > self.printer_image_max_width:
                    if event.x > self.start_x:
                        x2 = self.start_x + self.printer_image_max_width
                    else:
                        x2 = self.start_x - self.printer_image_max_width
            
            y2 = event.y

            self.canvas.coords(self.rect_id, self.start_x, self.start_y, x2, y2)


    def on_mouse_release(self, event):
        """
        マウスの左ボタンが離されたときの処理。
        """
        if self.rect_id:
            # 矩形の最終的な座標を取得
            x1, y1, x2, y2 = self.canvas.coords(self.rect_id)

            # 幅と高さを計算
            current_width = abs(x2 - x1)
            current_height = abs(y2 - y1)

            self.selection_window.destroy()  # 矩形選択ウィンドウを閉じる

            # 幅を制限
            if self.widthforce_mode.get():
                # 横幅が超える場合
                if current_width > self.printer_image_max_width:
                    if event.x > self.start_x:
                        x2 = self.start_x + self.printer_image_max_width
                    else:
                        x2 = self.start_x - self.printer_image_max_width

            # スクリーンショットを取得
            self.take_screenshot(x1, y1, x2, y2)

            # 自分のウィンドウを再表示する
            self.deiconify()


    def on_drop(self, event):
        """
        ドロップされたファイルを処理
        """
        file_path = event.data.strip()  # ドロップされたファイルのパス
        file_path = os.path.normpath(file_path)  # パスを正規化

        # ファイル名に空白を含と{}で返されるので除去
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]

        # 画像ファイルかどうかを確認
        if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            messagebox.showerror("エラー", "画像ファイルをドロップしてください。")
            return

        try:
            # 画像を読み込む
            image = Image.open(file_path)
            # 90度回転読込が有効の場合
            if self.rotate_load_enabled.get():
                # 画像の回転方向を設定
                if self.config.get("rotate_direction", "clockwise") == "clockwise":
                    # 時計回りに90度回転
                    image = image.rotate(-90, expand=True)
                else:
                    # 反時計回りに90度回転
                    image = image.rotate(90, expand=True)
            # 元の画像を保存
            self.original_image = image.copy()
            # キャンバス反映
            self.update_preview(image)

        except Exception as e:
            self.show_error(f"画像の読み込み中にエラーが発生しました:\n{e}")


    def enable_image_drag(self):
        """
        Canvas上で画像をドラッグして移動できるようにする。
        """
        if self.processed_image is None:
            return

        # 画像サイズを取得
        img_w, img_h = self.processed_image.size
        # フォーム上のキャンバスのサイズを取得
        canvas_w = int(self.picture_canvas["width"])
        canvas_h = int(self.picture_canvas["height"])

        # 画像がキャンバスより小さい、同じならドラッグ不要
        if img_w <= canvas_w and img_h <= canvas_h:
            self.picture_canvas.config(cursor="arrow") # カーソルを戻す
            return

        self.picture_canvas.config(cursor="fleur") # カーソル変更
      
        def start_drag(event):
            # ドラッグ開始位置を記録
            self.drag_start_x = event.x
            self.drag_start_y = event.y

        def drag_image(event):
            # 現在の画像の位置を取得
            current_coords = self.picture_canvas.coords(self.image_id)
            current_x, current_y = current_coords[0], current_coords[1]

            # 移動量を計算
            dx = event.x - self.drag_start_x
            dy = event.y - self.drag_start_y

            # 新しい位置を計算
            new_x = current_x + dx
            new_y = current_y + dy

            # キャンバスの可視サイズを取得
            canvas_w = int(self.picture_canvas["width"])
            canvas_h = int(self.picture_canvas["height"])

            # 画像の幅と高さを取得
            image_w = self.image_tk.width()
            image_h = self.image_tk.height()

            # 画像の移動範囲を制限(X座標)
            if image_w > canvas_w:
                min_x = canvas_w - image_w
                max_x = 0
                new_x = max(min(new_x, max_x), min_x)
                dx = new_x - current_x
            else:
                dx = 0
        
            # 画像の移動範囲を制限(Y座標)
            if image_h > canvas_h:
                min_y = canvas_h - image_h
                max_y = 0
                new_y = max(min(new_y, max_y), min_y)
                dy = new_y - current_y
            else:
                dy = 0

            # 画像を移動
            self.picture_canvas.move(self.image_id, dx, dy)

            # ドラッグ開始位置を更新
            self.drag_start_x = event.x
            self.drag_start_y = event.y

        # ドラッグイベントをバインド
        self.picture_canvas.bind("<ButtonPress-1>", start_drag)
        self.picture_canvas.bind("<B1-Motion>", drag_image)


    def take_screenshot(self, x1, y1, x2, y2):
        """
        指定された矩形領域のスクリーンショットを取得して表示します。
        """
        try:
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            # 90度回転読込が有効の場合
            if self.rotate_load_enabled.get():
                if self.config.get("rotate_direction", "clockwise") == "clockwise":
                    # 時計回りに90度回転
                    screenshot = screenshot.rotate(-90, expand=True)
                else:
                    # 反時計回りに90度回転
                    screenshot = screenshot.rotate(90, expand=True)
            # 元の画像を保存
            self.original_image = screenshot.copy()
            # キャンバス反映
            self.update_preview(screenshot)

        except Exception as e:
            messagebox.showerror("エラー(take_screenshot)", f"スクリーンショットの取得中にエラーが発生しました:\n{e}")


    def insert_barcode_tag(self, tag, content):
        self.text_widget.insert("insert", f"<{tag}:{content}>")
        self.apply_barcode_tags()


    def apply_barcode_tags(self):
        content = self.text_widget.get("1.0", "end-1c")
        for bc in BARCODE_TAGS.values():
            self.text_widget.tag_remove(bc["tag"], "1.0", "end")
            for match in re.finditer(bc["pattern"], content):
                start = f"1.0+{match.start()}c"
                end   = f"1.0+{match.end()}c"
                self.text_widget.tag_add(bc["tag"], start, end)

    def reapply_alignment_tags(self):
        """
        テキストウィジェット内の<ALIGN:...>タグを再適用します。
        """
        self.text_widget.tag_remove("align_left", "1.0", "end")
        self.text_widget.tag_remove("align_center", "1.0", "end")
        self.text_widget.tag_remove("align_right", "1.0", "end")
        # 既存の配置タグ・色タグを一旦削除
        for tag_info in CUSTOM_TAGS.values():
            self.text_widget.tag_remove(tag_info["tag"], "1.0", "end")
            # 配置用タグ（例: align_left, align_center, align_right）も必要に応じて削除
            align_tag = tag_info["tag"].replace("_color", "")
            self.text_widget.tag_remove(align_tag, "1.0", "end")

        lines = self.text_widget.get("1.0", "end-1c").splitlines()
        current_align = "align_left"  # デフォルトは左寄せ
        line_number = 1

        # カスタムタグの色を設定
        #for tag_info in CUSTOM_TAGS.values():
        #    keyword = tag_info["pattern"]
        #    tag = tag_info["tag"]
        #    start = "1.0"
        #    while True:
        #        pos = self.text_widget.search(keyword, start, stopindex="end")
        #        if not pos:
        #            break
        #        end = f"{pos}+{len(keyword)}c"
        #        self.text_widget.tag_add(tag, pos, end)
        #        start = end

        line_count = int(self.text_widget.index("end-1c").split('.')[0])
        for i in range(1, line_count + 1):
            line_start = f"{i}.0"
            line_end = f"{i}.end"
            line_text = self.text_widget.get(line_start, line_end)

            for tag_info in CUSTOM_TAGS.values():
                pattern = tag_info["pattern"]
                if line_text.startswith(pattern):
                    tag_len = len(pattern)
                    tag_name = tag_info["tag"]
                    # タグ設定（既に設定済みなら上書きでもOK）
                    self.text_widget.tag_configure(
                        tag_name,
                        background=tag_info["bg"],
                        foreground=tag_info["fg"]
                    )
                    # 先頭部分にタグを付与
                    self.text_widget.tag_add(
                        tag_name,
                        line_start,
                        f"{line_start}+{tag_len}c"
                    )
                    break  # 1行に複数のALIGNタグが先頭に来ることはない前提

        # 各先頭行に <ALIGN:...> タグのパターン
        pattern = r"^<ALIGN:(LEFT|CENTER|RIGHT)>"
        # 各行を確認してタグを適用
        for line in lines:
            tag_line = line
            # 現在の行のタグを確認
            for match in re.finditer(pattern, tag_line):
                align_type = match.group(1)
                if align_type == "LEFT":
                    current_align = "align_left"
                    #keyword = "<ALIGN:LEFT>"
                    #end = f"{line_number}+{len(keyword)-2}c"
                    #line_end = f"{line_number}.end"
                    #print(f"Line {line_end}: line_end")
                    #elf.text_widget.tag_add("align_center_color", f"{line_number}.0",end)
                    #self.text_widget.tag_add("align_center_color", f"{line_number}.0", f"{6}.c")
                    print(f"Line {line_number}: align left")
                elif align_type == "CENTER":
                    current_align = "align_center"
                    #self.text_widget.tag_add("align_center_color", f"{line_number}.0", f"{6}.c")
                    print(f"Line {line_number}: align center")
                elif align_type == "RIGHT":
                    current_align = "align_right"
                    print(f"Line {line_number}: align right")

            self.text_widget.tag_add(current_align, f"{line_number}.0", f"{line_number}.end")
            line_number += 1


    def input_qr_barcode(self):
        """
        QRコードを入力
        """
        while True:
            dlg = InptDialog(self, title="QRコード", prompt="QRコードに埋め込む情報（最大256文字）:")
            data = dlg.result
            if data is None:
                return
            if len(data) > 256:
                messagebox.showerror("エラー", "最大256文字までです。")
            else:
                self.insert_barcode_tag("QR", data)
                return


    def input_itf_barcode(self):
        """
        ITFコードを入力
        """
        while True:
            dlg = InptDialog(self, title="ITF", prompt="偶数桁の数字を入力してください(奇数桁は先頭に0が自動追加):")
            data = dlg.result
            if data is None:
                return
            if data.isdigit():
                if len(data) % 2 != 0:
                    data = "0" + data # 奇数桁の場合は先頭に0を追加
                    messagebox.showinfo("情報", "奇数桁のため、先頭に0を追加しました。")
                self.insert_barcode_tag("ITF", data)
                return
            else:
                messagebox.showerror("エラー", "数字のみ有効です。")


    def input_ean13_barcode(self):
        """
        EAN13コードを入力(12桁または13桁)
        """
        while True:
            dlg = InptDialog(self, title="EAN13", prompt="12または13桁の数字を入力してください:")
            data = dlg.result
            if data is None:
                return
            if data.isdigit() and len(data) in (12, 13):
                self.insert_barcode_tag("EAN13", data)
                return
            else:
                messagebox.showerror("エラー", "12または13桁の数字のみ有効です。")


    def input_code39_barcode(self):
        """
        Code39コードを入力
        """
        while True:
            dlg = InptDialog(self, title="Code39", prompt="英大文字/数字/記号 (- . $ / + % 空白) のみ有効:")
            data = dlg.result
            if data is None:
                return
            if re.fullmatch(r"[A-Z0-9\-.$/+% ]+", data.upper()):
                self.insert_barcode_tag("C39", data.upper())
                return
            else:
                messagebox.showerror("エラー", "使用できない文字が含まれています。")


    def input_code128_barcode(self):
        """
        Code128コードを入力
        """
        while True:
            dlg = InptDialog(self, title="Code128", prompt="ASCII文字列（最大90文字）:")
            data = dlg.result
            if data is None:
                return
            try:
                data.encode("ascii")
                if len(data) > 90:
                    messagebox.showerror("エラー", "最大90文字までです。")
                else:
                    self.insert_barcode_tag("B128", data)
                    return
            except UnicodeEncodeError:
                messagebox.showerror("エラー", "ASCII文字のみ使用できます。")


    def insert_horizontal_rule(self):
        """
        水平罫線を入力
        """
        self.text_widget.insert("insert", "<HR>")  # <HR>タグを挿入


    def insert_align_left(self):
        """
        左寄せを入力
        """
        self.text_widget.insert("insert", "<ALIGN:LEFT>\n")  # <ALIGN:LEFT>タグを挿入
        self.reapply_alignment_tags()
    

    def insert_align_center(self):
        """
        中央寄せを入力
        """
        self.text_widget.insert("insert", "<ALIGN:CENTER>\n")  # <ALIGN:CENTER>タグを挿入
        self.reapply_alignment_tags()

    
    def insert_align_right(self):
        """
        右寄せを入力
        """
        self.text_widget.insert("insert", "<ALIGN:RIGHT>\n")  # <ALIGN:RIGHT>タグを挿入
        self.reapply_alignment_tags()


    def print(self):
        """
        サーマルプリンタで印字します。
        """
        # チェック
        printer_ip = self.config.get("printer_ip", "")
        if not printer_ip:
            messagebox.showerror("エラー", "プリンターのIPアドレスが設定されていません。")
            return

        try:
            printer = PrinterHandler(ip_address=printer_ip, config=self.tm88iv_config)
            printer.print_text_with_tags(text_widget=self.text_widget,
                                         image_path=self.processed_image,
                                         enable_text_print=self.text_out_enabled.get(),
                                         enable_image_print=self.image_out_enabled.get(),
                                         should_cut_paper=self.paper_cut_enabled.get())
        except Exception as e:
            self.show_error(f"印字中にエラーが発生しました:\n{e}")


    def start_thread_tray(self):
        """
        タスクトレイアイコンのスレッドを開始
        """
        menu = Menu(
            MenuItem("フォームを表示", lambda: self.after(0, self.deiconify)),
            MenuItem("終了", lambda: self.after(0, self.stop_thread_tray))
        )
        icon_image = Image.open(self.src_dir / "minicaptureprint.ico")
        self.icon = Icon("MiniCapturePrint", icon_image, "MiniCapturePrint", menu)
        self.icon.run()


    def stop_thread_tray(self):
        """
        タスクトレイアイコンのスレッドを停止
        """
        try:
            # タスクトレイアイコンを停止
            if self.icon:
                self.icon.stop()
        except Exception as e:
            messagebox.showerror("エラー", f"タスクトレイアイコンの停止中に問題が発生しました:\n{e}")

        try:
            # Tkinterのウィンドウを破棄
            if self:
                self.destroy()
        except Exception as e:
            messagebox.showerror("エラー", f"ウィンドウの破棄中に問題が発生しました:\n{e}")

        # 終了
        sys.exit(0)


    def on_minimize(self, event=None):
        """
        最小化ボタンが押されたときにタスクバーから非表示
        """
        self.withdraw()
    

    def on_close(self):
        """
            閉じるボタンが押されたときにアプリケーションを終了
        """
        self.stop_thread_tray()


    def run(self):
        """
        アプリケーションを実行
        """
        threading.Thread(target=self.start_thread_tray, daemon=True).start()
        self.mainloop()


# アプリケーションのエントリポイント
if __name__ == "__main__":
    app = App()
    app.run()
