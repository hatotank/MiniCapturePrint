import sys
from pathlib import Path

from escpos.printer import Network
from tm88iv.tm88iv import TM88IV


class PrinterHandler:
    def __init__(self, ip_address, media_width=512):

        config = {
            "jis0201_file": "../data/JIS0201.TXT",  # JIS0201 データファイル
            "jis0208_file": "../data/JIS0208.TXT",  # JIS0208 データファイル
            "jis0212_file": "../data/JIS0212.TXT",  # JIS0212 データファイル
            "jis0213_file": "../data/JIS0213-2004.TXT",  # JIS0213-2004 データファイル
            "emoji_font_file": "../fonts/OpenMoji-black-glyf.ttf",  # OpenMoji フォント
            "kanji_font_file": "../fonts/NotoSansJP-Medium.otf",  # 日本語フォント
            "fallback_font_file": "../fonts/unifont_jp-16.0.03.otf",  # フォールバックフォント
        }
        #self.printer = Network(ip_address)
        self.ip = ip_address
        self.tm_print = TM88IV(self.ip, config=config)  # TM88IVのインスタンスを作成
        #self.tm_print.profile.profile_data
        #self.printer.media_width = media_width
        # python-escpos ver3.1にて確認
        #self.printer.profile.profile_data['media']['width']['pixels'] = media_width
        #print(f"設定されたプロファイル: {self.printer.profile.profile_data}")
        pass

    def print_text_with_tags(self, text_widget,image_path=None,cut=False):
        parser = TextTagParser(text_widget)
        #tm_print = TM88IV(self.ip)
        #tm_print.
        isprinted = False  # 印刷フラグ
        text = text_widget.get("1.0", "end")

        if not text.strip() and not image_path:
            return

        self.tm_print.open()  # プリンタを開く
        print(f"印刷するテキスト: {text.strip()}")  # デバッグ用に出力
        if text.strip():
            self.tm_print.jptext2(text)  # テキストを取得して印刷
            isprinted = True  # 印刷フラグを設定
        if image_path:
            self.tm_print.image(image_path)
            isprinted = True  # 画像印刷フラグを設定
        
        
        #tm_print.jptext2("あaiueo")  # テキストを取得して印刷
        #commands = parser.parse()
        print("=== ESCコマンドの送信を開始 ===")
        #for cmd in commands:
            #self._raw(cmd)
        #    print(f"ESCコマンド: {cmd}")  # デバッグ用に出力
        #pass
        if isprinted and cut:
            self.tm_print.cut()  # カットコマンドを送信
        self.tm_print.close()  # プリンタを閉じる
        #self.printer.cut()
        #self.printer.close()


    def print_text(self, text):
        try:
            self.printer.text(text)
            self.printer.cut()
        except Exception as e:
            print(f"プリンタエラー: {e}")
        finally:
            # プリンタを閉じる
            self.printer.close()

    def print_image(self, image_path):
        """
        画像を印刷します。
        """
        try:
            # 画像を印刷
            #self.printer.hw("INIT")
            self.printer.image(image_path)
            self.printer.cut()
        except Exception as e:
            print(f"プリンタエラー: {e}")
        finally:
            # プリンタを閉じる
            self.printer.close()

class TextTagParser:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.esc_commands = []  # 最終的にPrinterHandlerへ渡すコマンド列

    def parse(self):
        self.esc_commands.clear()
        total_lines = int(self.text_widget.index("end-1c").split(".")[0])

        for lineno in range(1, total_lines + 1):
            line_start = f"{lineno}.0"
            line_end = f"{lineno}.end"
            line_text = self.text_widget.get(line_start, line_end)

            active_tags = self._get_tags_in_range(line_start, line_end)

            # ESC/POSコマンドに変換
            esc_line = self._convert_line_to_esc(line_text, active_tags)
            self.esc_commands.extend(esc_line)

        return self.esc_commands

    def _get_tags_in_range(self, start, end):
        tags = set()
        for tag in self.text_widget.tag_names():
            for i in range(0, len(self.text_widget.tag_ranges(tag)), 2):
                rng_start = self.text_widget.tag_ranges(tag)[i]
                rng_end = self.text_widget.tag_ranges(tag)[i + 1]
                if (self.text_widget.compare(rng_start, "<", end) and
                        self.text_widget.compare(rng_end, ">", start)):
                    tags.add(tag)
                    break
        return tags

    def _convert_line_to_esc(self, text, tags):
        commands = []

        # 倍角処理
        if "bold" in tags:
            pass
    
        return commands