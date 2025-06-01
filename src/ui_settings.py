from tkinter import Button, Label, Toplevel, Frame, LabelFrame, Entry, Radiobutton, Checkbutton, BooleanVar, StringVar, messagebox
import ipaddress
import re

class SettingsWindow(Toplevel):
    def __init__(self, master, config):
        """
        設定ウィンドウの初期化
        :param master: 親ウィンドウ
        :param config: 設定データ
        """
        super().__init__(master)
        self.title("設定（設定内容の反映はアプリ再起動後です）")
        self.geometry("620x600")
        self.resizable(False, False)
        # 常に最前面に表示
        self.attributes("-topmost", True)
        # フォーカスを強制的に当てる
        self.focus_force()
        # ウィンドウを閉じるときの処理
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.config_data = config

        self.printer_ip = StringVar()
        self.printer_port = StringVar()
        self.image_max_width = StringVar()
        self.image_max_height = StringVar()
        self.startup_mode = StringVar()
        self.hotkey_enabled = BooleanVar()
        self.hotkey_combination = None # Entryウィジェットは後で作成
        self.rotate_direction = StringVar()
        self.edge_detection = StringVar()
        self.dither_pattern = StringVar()
        self.matrix_size = StringVar()

        self.create_widgets()
        self.load_config()


    def on_close(self):
        """
        ウィンドウを閉じるときの処理
        """
        # 最前面属性を解除
        self.attributes("-topmost", False)
        self.destroy()


    def create_widgets(self):
        """
        ウィジェットを作成するメソッド
        """
        # ラベルフレーム：プリンタ設定
        options_frame1 = LabelFrame(self, text="プリンタ設定")
        options_frame1.place(x=10, y=10, width=490, height=140)
        # IPアドレス
        label1 = Label(options_frame1, text="IPアドレス")
        label1.place(x=5, y=5, height=21)
        self.printer_ip = Entry(options_frame1, width=20)
        self.printer_ip.place(x=10, y=30, height=21)
        # ポート番号
        label2 = Label(options_frame1, text="ポート番号")
        label2.place(x=5, y=55, height=21)
        self.printer_port = Entry(options_frame1, width=20)
        self.printer_port.place(x=10, y=80, height=21)
        # 最大画像幅(横／ピクセル)
        label3 = Label(options_frame1, text="最大画像幅(横／ピクセル)")
        label3.place(x=200, y=5, height=21)
        self.image_max_width = Entry(options_frame1, width=20)
        self.image_max_width.place(x=205, y=30, height=21)
        # 最大画像幅(縦／ピクセル)
        label4 = Label(options_frame1, text="最大画像幅(縦／ピクセル)")
        label4.place(x=200, y=55, height=21)
        self.image_max_height = Entry(options_frame1, width=20)
        self.image_max_height.place(x=205, y=80, height=21)

        # ラベルフレーム：基本動作
        options_frame2 = LabelFrame(self, text="基本動作")
        options_frame2.place(x=10, y=160, width=490, height=230)
        # 起動モード(フォーム表示/タスクトレイ)
        label10 = Label(options_frame2, text="起動モード")
        label10.place(x=5, y=5, height=21)
        radiobutton10 = Radiobutton(options_frame2, text="フォーム表示", variable=self.startup_mode, value="form")
        radiobutton10.place(x=10, y=30, height=21)
        radiobutton20 = Radiobutton(options_frame2, text="タスクトレイ", variable=self.startup_mode, value="tray")
        radiobutton20.place(x=120, y=30, height=21)
        # ホットキー有効化
        label11 = Label(options_frame2, text="ホットキー有効化")
        label11.place(x=5, y=55, height=21)
        checkbutton10 = Checkbutton(options_frame2, text="有効", variable=self.hotkey_enabled, command=self._toggle_hotkey_combination)
        checkbutton10.place(x=10, y=80, height=21)
        # ホットキー組み合わせ
        label12 = Label(options_frame2, text="ホットキー組み合わせ")
        label12.place(x=5, y=105, height=21)
        self.hotkey_combination = Entry(options_frame2, width=50)
        self.hotkey_combination.place(x=10, y=130, height=21)
        # キャプチャ時の回転方向(時計回り/反時計回り)
        label13 = Label(options_frame2, text="キャプチャ時の回転方向")
        label13.place(x=5, y=155, height=21)
        radiobutton13 = Radiobutton(options_frame2, text="時計回り", variable=self.rotate_direction, value="clockwise")
        radiobutton13.place(x=10, y=180, height=21)
        radiobutton14 = Radiobutton(options_frame2, text="反時計回り", variable=self.rotate_direction, value="counterclockwise")
        radiobutton14.place(x=120, y=180, height=21)

        # ラベルフレーム：高度な設定
        options_frame3 = LabelFrame(self, text="高度な設定(ハイブリッドディザ用)")
        options_frame3.place(x=10, y=400, width=490, height=190)
        # エッジ検出(FIND_EDGES/EDGE_ENHANCE/EDGE_ENHANCE_MORE/CONTOUR)
        label20 = Label(options_frame3, text="エッジ検出")
        label20.place(x=5, y=5, height=21)
        radiobutton100 = Radiobutton(options_frame3, text="FIND_EDGES", variable=self.edge_detection, value="FIND_EDGES")
        radiobutton100.place(x=10, y=30, height=21)
        radiobutton200 = Radiobutton(options_frame3, text="EDGE_ENHANCE", variable=self.edge_detection, value="EDGE_ENHANCE")
        radiobutton200.place(x=130, y=30, height=21)
        radiobutton300 = Radiobutton(options_frame3, text="ENHANCE_MORE", variable=self.edge_detection, value="EDGE_ENHANCE_MORE")
        radiobutton300.place(x=250, y=30, height=21)
        radiobutton400 = Radiobutton(options_frame3, text="CONTOUR", variable=self.edge_detection, value="CONTOUR")
        radiobutton400.place(x=370, y=30, height=21)
        # ディザパターン変更(bayer/random/clustered)
        label21 = Label(options_frame3, text="ディザパターン変更")
        label21.place(x=5, y=55, height=21)
        radiobutton110 = Radiobutton(options_frame3, text="bayer", variable=self.dither_pattern, value="bayer")
        radiobutton110.place(x=10, y=80, height=21)
        radiobutton210 = Radiobutton(options_frame3, text="random", variable=self.dither_pattern, value="random")
        radiobutton210.place(x=130, y=80, height=21)
        radiobutton310 = Radiobutton(options_frame3, text="clustered", variable=self.dither_pattern, value="clustered")
        radiobutton310.place(x=250, y=80, height=21)
        # マトリクス数(2/4/8)
        label22 = Label(options_frame3, text="マトリクス数")
        label22.place(x=5, y=105, height=21)
        radiobutton120 = Radiobutton(options_frame3, text="2", variable=self.matrix_size, value="2")
        radiobutton120.place(x=10, y=130, height=21)
        radiobutton220 = Radiobutton(options_frame3, text="4", variable=self.matrix_size, value="4")
        radiobutton220.place(x=130, y=130, height=21)
        radiobutton320 = Radiobutton(options_frame3, text="8", variable=self.matrix_size, value="8")
        radiobutton320.place(x=250, y=130, height=21)

        # ボタン配置
        Button(self, text="保存", command=self.save_config).place(x=510, y=18, width=100, height=30)
        Button(self, text="キャンセル", command=self.destroy).place(x=510, y=58, width=100, height=30)


    def load_config(self):
        """
        設定値を読み込むメソッド
        """
        # config_dataからの読み込み（初期値処理）
        # IPアドレス
        self.printer_ip.delete(0, "end")
        self.printer_ip.insert(0, self.config_data.get("printer_ip", "192.168.10.21"))
        if self._validate_ip(silent=True) is False:
            messagebox.showwarning("警告", "IPアドレスが無効です。初期値に値に戻します。")
            self.printer_ip.set("192.168.10.21")

        # ポート番号
        self.printer_port.delete(0, "end")
        self.printer_port.insert(0, self.config_data.get("printer_port", "9100"))
        if self._validate_port(silent=True) is False:
            messagebox.showwarning("警告", "ポート番号が無効です。初期値に値に戻します。")
            self.printer_port.set("9100")

        # 最大画像幅(横／ピクセル)
        self.image_max_width.delete(0, "end")
        self.image_max_width.insert(0, self.config_data.get("image_max_width", "512"))
        if self._validate_max_image_width(silent=True) is False:
            messagebox.showwarning("警告", "最大画像幅(横)が無効です。初期値に値に戻します。")
            self.image_max_width.set("512")
        
        # 最大画像幅(縦／ピクセル)
        self.image_max_height.delete(0, "end")
        self.image_max_height.insert(0, self.config_data.get("image_max_height", "960"))
        if self._validate_max_image_height(silent=True) is False:
            messagebox.showwarning("警告", "最大画像幅(縦)が無効です。初期値に値に戻します。")
            self.image_max_height.set("960")

        # 起動モード
        startup_mode = self.config_data.get("startup_mode", "form")
        if startup_mode == "form":
            self.startup_mode.set("form")
        elif startup_mode == "tray":
            self.startup_mode.set("tray")
        if self._validate_startup_mode(silent=True) is False:
            messagebox.showwarning("警告", "起動モードが無効です。初期値に値に戻します。")
            self.startup_mode.set("form")

        # ホットキー有効化
        self.hotkey_enabled.set(self.config_data.get("hotkey_enabled", True))
        if self._validate_hotkey_enabled(silent=True) is False:
            messagebox.showwarning("警告", "ホットキー有効化が無効です。初期値に値に戻します。")
            self.hotkey_enabled.set(True)

        # ホットキー組み合わせ
        self.hotkey_combination.delete(0, "end")
        self.hotkey_combination.insert(0, self.config_data.get("hotkey_combination", "ctrl+alt+shift+c"))
        if self._validate_hotkey_combination(silent=True) is False:
            messagebox.showwarning("警告", "ホットキー組み合わせが無効です。初期値に値に戻します。")
            self.hotkey_combination.set("ctrl+alt+shift+c")

        # キャプチャ時の回転方向
        rotate_direction = self.config_data.get("rotate_direction", "clockwise")
        if rotate_direction == "clockwise":
            self.rotate_direction.set("clockwise")
        elif rotate_direction == "counterclockwise":
            self.rotate_direction.set("counterclockwise")
        if self._validate_rotate_direction(silent=True) is False:
            messagebox.showwarning("警告", "キャプチャ時の回転方向が無効です。初期値に値に戻します。")
            self.rotate_direction.set("clockwise")

        # エッジ検出
        edge_detection = self.config_data.get("edge_detection", "FIND_EDGES")
        if edge_detection == "FIND_EDGES":
            self.edge_detection.set("FIND_EDGES")
        elif edge_detection == "EDGE_ENHANCE":
            self.edge_detection.set("EDGE_ENHANCE")
        elif edge_detection == "EDGE_ENHANCE_MORE":
            self.edge_detection.set("EDGE_ENHANCE_MORE")
        elif edge_detection == "CONTOUR":
            self.edge_detection.set("CONTOUR")
        if self._validate_edge_detection(silent=True) is False:
            messagebox.showwarning("警告", "エッジ検出が無効です。初期値に値に戻します。")
            self.edge_detection.set("FIND_EDGES")

        # ディザパターン変更
        dither_pattern = self.config_data.get("dither_pattern", "bayer")
        if dither_pattern == "bayer":
            self.dither_pattern.set("bayer")
        elif dither_pattern == "random":
            self.dither_pattern.set("random")
        elif dither_pattern == "clustered":
            self.dither_pattern.set("clustered")
        if self._validate_dither_pattern(silent=True) is False:
            messagebox.showwarning("警告", "ディザパターン変更が無効です。初期値に値に戻します。")
            self.dither_pattern.set("bayer")

        # マトリクス数
        matrix_size = int(self.config_data.get("matrix_size", 4))
        if matrix_size == 2:
            self.matrix_size.set(2)
        elif matrix_size == 4:
            self.matrix_size.set(4)
        elif matrix_size == 8:
            self.matrix_size.set(8)
        if self._validate_matrix_size(silent=True) is False:
            messagebox.showwarning("警告", "マトリクス数が無効です。初期値に値に戻します。")
            self.matrix_size.set(4)

        # ホットキー組み合わせの有効/無効を切り替え
        self._toggle_hotkey_combination()


    def save_config(self):
        """
        設定値を保存するメソッド
        """
        # 入力値のバリデーション
        if not self.validate_inputs(silent=False):
            return
        
        # config_dataへの保存
        # IPアドレス
        self.config_data.set("printer_ip", self.printer_ip.get())
        # ポート番号
        self.config_data.set("printer_port", self.printer_port.get())
        # 最大画像幅(横／ピクセル)
        self.config_data.set("image_max_width", self.image_max_width.get())
        # 最大画像幅(縦／ピクセル)
        self.config_data.set("image_max_height", self.image_max_height.get())
        # 起動モード
        self.config_data.set("startup_mode", self.startup_mode.get())
        # ホットキー有効化
        self.config_data.set("hotkey_enabled", self.hotkey_enabled.get())
        # ホットキー組み合わせ
        self.config_data.set("hotkey_combination", self.hotkey_combination.get())
        # キャプチャ時の回転方向
        self.config_data.set("rotate_direction", self.rotate_direction.get())
        # エッジ検出
        self.config_data.set("edge_detection", self.edge_detection.get())
        # ディザパターン変更
        self.config_data.set("dither_pattern", self.dither_pattern.get())
        # マトリクス数
        self.config_data.set("matrix_size", self.matrix_size.get())

        # 設定を保存
        self.config_data.save_config()
        # ウィンドウを閉じる
        self.destroy()


    def validate_inputs(self, silent=False):
        """
        入力値のバリデーションを行うメソッド
        """
        return (
            self._validate_ip(silent) and
            self._validate_port(silent) and
            self._validate_max_image_width(silent) and
            self._validate_max_image_height(silent) and
            self._validate_startup_mode(silent) and
            self._validate_hotkey_enabled(silent) and
            self._validate_hotkey_combination(silent) and
            self._validate_rotate_direction(silent) and
            self._validate_edge_detection(silent) and
            self._validate_dither_pattern(silent) and
            self._validate_matrix_size(silent)
        )

    def _validate_ip(self, silent):
        """
        IPアドレスの検証
        """
        try:
            ipaddress.ip_address(self.printer_ip.get())
            return True
        except ValueError:
            if not silent:
                messagebox.showerror("エラー", "無効なIPアドレス指定です（例: 192.168.10.21）")
            return False

    def _validate_port(self, silent):
        """
        ポート番号の検証
        """
        try:
            port = int(self.printer_port.get())
            if port < 1 or port > 65535:
                if not silent:
                    raise messagebox.showerror("ポート番号は1から65535の範囲で指定してください（例: 9100）")
                return False
            return True
        except ValueError:
            if not silent:
                messagebox.showerror("エラー", "ポート番号は整数で指定してください（例: 9100）")
            return False

    def _validate_max_image_width(self, silent):
        """
        最大画像幅(横)の検証
        """
        if not self.image_max_width.get().isdigit(): 
            if not silent:
                messagebox.showerror("エラー", "最大画像幅は整数で指定してください")
            return False
        return True

    def _validate_max_image_height(self, silent):
        """
        最大画像幅(縦)の検証
        """
        if not self.image_max_height.get().isdigit(): 
            if not silent:
                messagebox.showerror("エラー", "最大画像幅は整数で指定してください")
            return False
        return True

    def _validate_startup_mode(self, silent):
        """
        起動モードの検証
        """
        if self.startup_mode.get() not in ["form", "tray"]:
            if not silent:
                messagebox.showerror("エラー", "起動モード指定が不正です（form または tray）")
            return False
        return True

    def _validate_hotkey_enabled(self, silent):
        """
        ホットキー有効化の検証
        """
        if not isinstance(self.hotkey_enabled.get(), bool):
            if not silent:
                messagebox.showerror("エラー", "ホットキー有効化の指定が不正です（True または False）")
            return False
        return True

    def _validate_hotkey_combination(self, silent):
        """
        ホットキー組み合わせの検証
        """
        if not self.hotkey_enabled.get():
            return True # ホットキー無効化時は検証しない

        lower_hotkey_combination = self.hotkey_combination.get().lower()
        if not re.match(r"(ctrl|alt|shift|\+|[a-z0-9])+", lower_hotkey_combination):
            if not silent:
                messagebox.showerror("エラー", "ホットキーの形式が不正です（例: ctrl+alt+c）")
            return False
        return True

    def _validate_rotate_direction(self, silent):
        """
        キャプチャ時の回転方向の検証
        """
        if self.rotate_direction.get() not in ["clockwise", "counterclockwise"]:
            if not silent:
                messagebox.showerror("エラー", "キャプチャ時の画像回転方向指定が不正です（clockwise または counterclockwise）")
            return False
        return True

    def _validate_edge_detection(self, silent):
        """
        エッジ検出の検証
        """
        if self.edge_detection.get() not in ["FIND_EDGES", "EDGE_ENHANCE", "EDGE_ENHANCE_MORE", "CONTOUR"]:
            if not silent:
                messagebox.showerror("エラー", "エッジ検出の指定が不正です（例: FIND_EDGES, EDGE_ENHANCE, EDGE_ENHANCE_MORE, CONTOUR）")
            return False
        return True

    def _validate_dither_pattern(self, silent):
        """
        ディザパターン変更の検証
        """
        if self.dither_pattern.get() not in ["bayer", "random", "clustered"]:
            if not silent:
                messagebox.showerror("エラー", "ディザパターンの指定が不正です（例: bayer, random, clustered）")
            return False
        return True

    def _validate_matrix_size(self, silent):
        """
        マトリクス数の検証（2のべき乗かつ許可値限定）
        """
        try:
            size = int(self.matrix_size.get())
            if size not in [2, 4, 8]:
                raise ValueError
            return True
        except ValueError:
            if not silent:
                messagebox.showerror("エラー", "マトリクスサイズは2, 4, 8のいずれかで指定してください")
            return False

    def _toggle_hotkey_combination(self):
        """
        ホットキー組み合わせの入力欄の有効/無効を切り替えるメソッド
        """
        if self.hotkey_enabled.get():
            self.hotkey_combination.config(state="normal")
        else:
            self.hotkey_combination.config(state="disabled")