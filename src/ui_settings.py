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
        self.emoji_font_enabled = BooleanVar()
        self.printer_emoji_font = StringVar()
        self.printer_emoji_font_size = StringVar()
        self.printer_emoji_font_adjust_x = StringVar()
        self.printer_emoji_font_adjust_y = StringVar()

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
        label_ip = Label(options_frame1, text="IPアドレス")
        label_ip.place(x=5, y=5, height=21)
        self.printer_ip = Entry(options_frame1, width=20)
        self.printer_ip.place(x=10, y=30, height=21)
        # ポート番号
        label_port = Label(options_frame1, text="ポート番号")
        label_port.place(x=5, y=55, height=21)
        self.printer_port = Entry(options_frame1, width=20)
        self.printer_port.place(x=10, y=80, height=21)
        # 最大画像幅(横／ピクセル)
        label_image_width = Label(options_frame1, text="最大画像幅(横／ピクセル)")
        label_image_width.place(x=200, y=5, height=21)
        self.image_max_width = Entry(options_frame1, width=20)
        self.image_max_width.place(x=205, y=30, height=21)
        # 最大画像幅(縦／ピクセル)
        label_image_height = Label(options_frame1, text="最大画像幅(縦／ピクセル)")
        label_image_height.place(x=200, y=55, height=21)
        self.image_max_height = Entry(options_frame1, width=20)
        self.image_max_height.place(x=205, y=80, height=21)

        # ラベルフレーム：基本動作
        options_frame2 = LabelFrame(self, text="基本動作")
        options_frame2.place(x=10, y=160, width=490, height=230)
        # 起動モード(フォーム表示/タスクトレイ)
        label_startup = Label(options_frame2, text="起動モード")
        label_startup.place(x=5, y=5, height=21)
        radio_startup_mode_from = Radiobutton(options_frame2, text="フォーム表示", variable=self.startup_mode, value="form")
        radio_startup_mode_from.place(x=10, y=30, height=21)
        radio_startup_mode_tray = Radiobutton(options_frame2, text="タスクトレイ", variable=self.startup_mode, value="tray")
        radio_startup_mode_tray.place(x=120, y=30, height=21)
        # ホットキー有効化
        label_hotkey = Label(options_frame2, text="ホットキー有効化(※非推奨)")
        label_hotkey.place(x=5, y=55, height=21)
        check_hotkey_enable = Checkbutton(options_frame2, text="有効(Pythonの仕様やWindows環境によっては、正常に動作しない場合があります)", variable=self.hotkey_enabled, command=self._toggle_hotkey_combination)
        check_hotkey_enable.place(x=10, y=80, height=21)
        # ホットキー組み合わせ
        label__hotkey_conbination = Label(options_frame2, text="ホットキー組み合わせ")
        label__hotkey_conbination.place(x=5, y=105, height=21)
        self.hotkey_combination = Entry(options_frame2, width=50)
        self.hotkey_combination.place(x=10, y=130, height=21)
        # キャプチャ時の回転方向(時計回り/反時計回り)
        label_rotate_direction = Label(options_frame2, text="キャプチャ時の回転方向")
        label_rotate_direction.place(x=5, y=155, height=21)
        label_rotate_direction_clockwise = Radiobutton(options_frame2, text="時計回り", variable=self.rotate_direction, value="clockwise")
        label_rotate_direction_clockwise.place(x=10, y=180, height=21)
        label_rotate_direction_counterclockwise = Radiobutton(options_frame2, text="反時計回り", variable=self.rotate_direction, value="counterclockwise")
        label_rotate_direction_counterclockwise.place(x=120, y=180, height=21)

        # ラベルフレーム：高度な設定
        options_frame3 = LabelFrame(self, text="高度な設定(絵文字フォント変更)")
        options_frame3.place(x=10, y=400, width=490, height=190)
        # 高度な設定有効化
        label_hotkey = Label(options_frame3, text="絵文字フォント変更有効化")
        label_hotkey.place(x=5, y=5, height=21)
        check_hotkey_enable = Checkbutton(options_frame3, text="有効", variable=self.emoji_font_enabled, command=self._toggle_emoji_settings)
        check_hotkey_enable.place(x=10, y=30, height=21)
        # フォントファイル名/フォントサイズ
        label_emoji_font = Label(options_frame3, text="フォントファイル名(dataフォルダに格納)")
        label_emoji_font.place(x=5, y=55, height=21)
        self.printer_emoji_font = Entry(options_frame3, width=20)
        self.printer_emoji_font.place(x=10, y=80, height=21)
        label_emoji_font_size = Label(options_frame3, text="フォントサイズ")
        label_emoji_font_size.place(x=200, y=55, height=21)
        self.printer_emoji_font_size = Entry(options_frame3, width=20)
        self.printer_emoji_font_size.place(x=205, y=80, height=21)
        # フォント位置調節(X座標/Y座標)
        label_emoji_adust_x = Label(options_frame3, text="フォント位置調節(X座標)")
        label_emoji_adust_x.place(x=5, y=105, height=21)
        label_emoji_adust_y = Label(options_frame3, text="フォント位置調節(Y座標)")
        label_emoji_adust_y.place(x=200, y=105, height=21)
        self.printer_emoji_font_adjust_x = Entry(options_frame3, width=20)
        self.printer_emoji_font_adjust_x.place(x=10, y=130, height=21)
        self.printer_emoji_font_adjust_y = Entry(options_frame3, width=20)
        self.printer_emoji_font_adjust_y.place(x=205, y=130, height=21)

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

        # 絵文字フォント変更有効化
        self.emoji_font_enabled.set(self.config_data.get("printer_emoji_font_enabled", False))
        if self._validate_emoji_enabled(silent=True) is False:
            messagebox.showwarning("警告", "絵文字フォント変更有効化が無効です。初期値に値に戻します。")
            self.emoji_font_enabled.set(False)

        # 絵文字フォント
        self.printer_emoji_font.delete(0, "end")
        self.printer_emoji_font.insert(0, self.config_data.get("printer_emoji_font", "OpenMoji-black-glyf.ttf"))
        if self._validate_emoji_font_file(silent=True) is False:
            messagebox.showwarning("警告", "絵文字フォントファイルが無効です。初期値に値に戻します。")
            self.printer_emoji_font.set("OpenMoji-black-glyf.ttf")

        # 絵文字フォントサイズ
        self.printer_emoji_font_size.delete(0, "end")
        self.printer_emoji_font_size.insert(0, self.config_data.get("printer_emoji_font_size", "20"))
        if self._validate_emoji_font_size(silent=True) is False:
            messagebox.showwarning("警告", "絵文字フォントサイズが無効です。初期値に値に戻します。")
            self.printer_emoji_font_size.set("20")

        # 絵文字フォント位置調節(X座標)
        self.printer_emoji_font_adjust_x.delete(0, "end")
        self.printer_emoji_font_adjust_x.insert(0, self.config_data.get("printer_emoji_font_adjust_x", "0"))
        if self._validate_emoji_font_adjust_x(silent=True) is False:
            messagebox.showwarning("警告", "絵文字フォント位置調節(X座標)が無効です。初期値に値に戻します。")
            self.printer_emoji_font_adjust_x.set("0")

        # 絵文字フォント位置調節(Y座標)
        self.printer_emoji_font_adjust_y.delete(0, "end")
        self.printer_emoji_font_adjust_y.insert(0, self.config_data.get("printer_emoji_font_adjust_y", "0"))
        if self._validate_emoji_font_adjust_y(silent=True) is False:
            messagebox.showwarning("警告", "絵文字フォント位置調節(Y座標)が無効です。初期値に値に戻します。")
            self.printer_emoji_font_adjust_y.set("0")

        # ホットキー組み合わせの有効/無効を切り替え
        self._toggle_hotkey_combination()
        # 絵文字フォント設定の有効/無効を切り替え
        self._toggle_emoji_settings()


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
        # 絵文字フォント変更有効化
        self.config_data.set("printer_emoji_font_enabled", self.emoji_font_enabled.get())
        # 絵文字フォントファイル名
        self.config_data.set("printer_emoji_font", self.printer_emoji_font.get())
        # 絵文字フォントサイズ
        self.config_data.set("printer_emoji_font_size", self.printer_emoji_font_size.get())
        # 絵文字フォント位置調節(X座標)
        self.config_data.set("printer_emoji_font_adjust_x", self.printer_emoji_font_adjust_x.get())
        # 絵文字フォント位置調節(Y座標)
        self.config_data.set("printer_emoji_font_adjust_y", self.printer_emoji_font_adjust_y.get())

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
            self._validate_emoji_enabled(silent) and
            self._validate_emoji_font_file(silent) and
            self._validate_emoji_font_size(silent) and
            self._validate_emoji_font_adjust_x(silent) and
            self._validate_emoji_font_adjust_y(silent)
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

    def _validate_emoji_enabled(self, silent):
        """
        絵文字フォント変更有効化の検証
        """
        if not isinstance(self.emoji_font_enabled.get(), bool):
            if not silent:
                messagebox.showerror("エラー", "絵文字フォント変更有効化の指定が不正です（True または False）")
            return False
        return True

    def _validate_emoji_font_file(self, silent):
        """
        絵文字フォントファイルの検証
        """
        if self.emoji_font_enabled.get() and not self.printer_emoji_font.get().isspace():
            if not silent:
                messagebox.showerror("エラー", "絵文字フォントファイル名が指定されていません")
            return False
        return True

    def _validate_emoji_font_size(self, silent):
        """
        絵文字フォントサイズの検証
        """
        try:
            size = int(self.printer_emoji_font_size.get())
            if size <= 0:
                raise ValueError
            return True
        except ValueError:
            if not silent:
                messagebox.showerror("エラー", "絵文字フォントサイズは正の整数で指定してください")
            return False

    def _validate_emoji_font_adjust_x(self, silent):
        """
        絵文字フォント位置調節(X座標)の検証
        """
        try:
            adjust_x = int(self.printer_emoji_font_adjust_x.get())
            return True
        except ValueError:
            if not silent:
                messagebox.showerror("エラー", "絵文字フォント位置調節(X座標)が不正です")
            return False

    def _validate_emoji_font_adjust_y(self, silent):
        """
        絵文字フォント位置調節(Y座標)の検証
        """
        try:
            adjust_y = int(self.printer_emoji_font_adjust_y.get())
            return True
        except ValueError:
            if not silent:
                messagebox.showerror("エラー", "絵文字フォント位置調節(Y座標)が不正です")
            return False

    def _toggle_hotkey_combination(self):
        """
        ホットキー組み合わせの入力欄の有効/無効を切り替えるメソッド
        """
        if self.hotkey_enabled.get():
            self.hotkey_combination.config(state="normal")
        else:
            self.hotkey_combination.config(state="disabled")

    def _toggle_emoji_settings(self):
        """
        絵文字フォント設定の有効/無効を切り替えるメソッド
        """
        if self.emoji_font_enabled.get():
            self.printer_emoji_font.config(state="normal")
            self.printer_emoji_font_size.config(state="normal")
            self.printer_emoji_font_adjust_x.config(state="normal")
            self.printer_emoji_font_adjust_y.config(state="normal")
        else:
            self.printer_emoji_font.config(state="disabled")
            self.printer_emoji_font_size.config(state="disabled")
            self.printer_emoji_font_adjust_x.config(state="disabled")
            self.printer_emoji_font_adjust_y.config(state="disabled")
