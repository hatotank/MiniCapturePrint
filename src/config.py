import json
import os
from tkinter import messagebox

class ConfigHandler:

    CONFIG_FILE = "../config/config.json"

    def __init__(self, config_file=CONFIG_FILE):
        """
        設定ファイルを読み込むクラス
        :param config_file: 設定ファイルのパス
        """
        self.config_file = config_file
        self.config = self.load_config()


    def load_config(self):
        """
        設定ファイルを読み込みます。
        設定ファイルが存在しない場合は空の辞書を返します。
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
        設定を保存します。
        """
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの保存中にエラーが発生しました:\n{e}")


    def get(self, key, default=None):
        """
        設定を取得します。
        :param key: 設定のキー
        :param default: デフォルト値
        :return: 設定の値
        """
        return self.config.get(key, default)


    def set(self, key, value):
        """
        設定を更新します。
        :param key: 設定のキー
        :param value: 設定の値
        """
        self.config[key] = value
        self.save_config()
