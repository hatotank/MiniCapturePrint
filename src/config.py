from pathlib import Path
from tkinter import messagebox
import json
import os

class ConfigHandler:
    """
    設定ファイルを読み書きするクラス
    """
    def __init__(self, config_file=Path("../config/config.json")):
        """
        設定ファイルを読み書きするクラス

        :param config_file: 設定ファイルのパス（Pathオブジェクト推奨）
        """
        # 文字列で渡された場合もPathに変換
        self.config_file = config_file if isinstance(config_file, Path) else Path(config_file)
        self.config_file = self.config_file.resolve()  # 絶対パスに変換
        self.config = self.load_config()

    def load_config(self):
        """
        設定ファイルを読み込み\n
        設定ファイルが存在しない場合は空の辞書を返却。

        :return: 設定の辞書
        :rtype: dict
        """
        if not os.path.exists(self.config_file):
            # 設定ファイルが存在しない場合は空の辞書を返す
            return {}
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            messagebox.showerror("エラー", f"設定ファイル '{self.config_file}' が見つかりません。")
            return {}
        except json.JSONDecodeError:
            messagebox.showerror("エラー", f"設定ファイル '{self.config_file}' の形式が正しくありません。")
            return {}

    def save_config(self):
        """
        設定を保存\n
        設定ファイルが存在しない場合は新規作成します。
        """
        try:
            # ディレクトリが存在しない場合は作成
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            # 設定をJSON形式で保存
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの保存中にエラーが発生しました:\n{e}")

    def get(self, key, default=None):
        """
        設定を取得

        :param key: 設定のキー
        :param default: デフォルト値
        :return: 設定の値
        """
        return self.config.get(key, default)


    def set(self, key, value):
        """
        設定を更新

        :param key: 設定のキー
        :param value: 設定の値
        """
        self.config[key] = value
