import sys
from pathlib import Path
import re
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
        # プリンタのメディア幅を設定(python-escpos ver3.1にて確認
        self.tm_print.profile.profile_data['media']['width']['pixels'] = media_width


    def print_text_with_tags(self, text_widget, image_path=None, enable_text_print=False, enable_image_print=False, should_cut_paper=False):
        """
        タグ付きテキストを印刷します。
        :param text_widget: タグ付きテキストを含むウィジェット
        :param image_path: 印刷する画像のパス
        :param enable_text_print: テキスト印刷を有効にするかどうか
        :param enable_image_print: 画像印刷を有効にするかどうか
        :param should_cut_paper: 印刷後に用紙をカットするかどうか
        """

        # デバッグ用のフラグ
        debug_print_enabled = True  # デバッグ用にプリントを無効化

        # タグ解析
        parser = TextTagParser(text_widget)
        commands = parser.parse()

        #isprinted = True  # 印刷フラグ
        #should_cut_paper = True  # 用紙をカットするかどうかのフラグ

        print(f"commands:--------------")
        if debug_print_enabled:
            print(f"=== 印刷開始 ===")
            self.tm_print.open()

            for arg_type, arg_command, arg_dict in commands:
                print(f"コマンド: {arg_type}, 引数: {arg_command}, オプション: {arg_dict}")
                if arg_type == "jp2":
                    self.tm_print.jptext2(arg_command, **arg_dict)  # テキストを取得して印刷
                    isprinted = True  # 印刷フラグを設定
                if arg_type == "qr":
                    self.tm_print.qr(arg_command,native=True)  # QRコードを印刷
                    isprinted = True  # 印刷フラグを設定
                if arg_type == "itf":
                    self.tm_print.barcode(arg_command, bc="ITF")  # ITFコードを印刷
                    isprinted = True  # 印刷フラグを設定
                if arg_type == "ean":
                    self.tm_print.barcode(arg_command, bc="EAN13")  # EANコードを印刷
                    isprinted = True  # 印刷フラグを設定
                if arg_type == "c39":
                    self.tm_print.barcode(arg_command, bc="CODE39")
                    isprinted = True  # 印刷フラグを設定
                if arg_type == "c128":
                    self.tm_print.barcode(arg_command, bc="CODE128")
                    isprinted = True  # 印刷フラグを設定
                if arg_type == "row":
                    self.tmp_print.row(arg_command)

            if enable_image_print:
                if image_path:
                    print(f"画像を印刷: {image_path}")
                    self.tm_print.image(image_path)
                    isprinted = True  # 画像印刷フラグを設定

            if isprinted and should_cut_paper:
                print("用紙をカットします")
                self.tm_print.cut()  # カットコマンドを送信

            print("=== 印刷完了 ===")
            self.tm_print.close()  # プリンタを閉じる


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

        self.blocks_per_line = self._get_line_tag_blocks()
        self.esc_commands = self._convert_line_to_esc()

        return self.esc_commands


    def _get_line_tag_blocks(self):
        """
        各行のタグブロックを取得
        """
        results = []
        total_lines = int(self.text_widget.index("end-1c").split(".")[0])
        for lineno in range(1, total_lines + 1):
            line_start = f"{lineno}.0"
            line_end = f"{lineno}.end"
            line_text = self.text_widget.get(line_start, line_end)
            # 1文字ごとの(文字, タグ)リスト
            segments = []
            index = line_start
            while True:
                next_index = self.text_widget.index(f"{index} +1c")
                if self.text_widget.compare(next_index, ">", line_end) or next_index == index:
                    break
                char = self.text_widget.get(index, next_index)
                tags = self.text_widget.tag_names(index)
                segments.append((char, tags))
                index = next_index
            # タグセットごとにブロック圧縮
            compressed = self._compress_tagged_segments(segments)
            results.append(compressed)
        return results


    def _compress_tagged_segments(self, segments):
        """
        タグ付きセグメントを圧縮する
        連続する同じタグの文字列を1つにまとめる
        """
        if not segments:
            return []

        compressed = []
        current_text = segments[0][0]
        current_tags = segments[0][1]

        for char, tags in segments[1:]:
            if tags == current_tags:
                current_text += char
            else:
                compressed.append((current_text, current_tags))
                current_text = char
                current_tags = tags

        compressed.append((current_text, current_tags))
        return compressed


    def _convert_line_to_esc(self):
        commands = []

        for line_blocks in self.blocks_per_line:

            # 行
            index = 0  # 行のインデックス
            for text, tags in line_blocks:
                row_dict = {}
                is_text = True  # テキストかどうかのフラグ
                jptext2_args_dict = {"bflg": True}
                print(f"'{text}' ---> {tags}")

                # 配置はテキストのタグを解釈する
                #if "align_left" in tags:
                #    commands.append(("row", b"\x1b\x61\x00", row_dict))
                #if "align_center" in tags:
                #    commands.append(("row", b"\x1b\x61\x01", row_dict))
                #if "align_right" in tags:
                #    commands.append(("row", b"\x1b\x61\x02", row_dict))

                # QRコード
                if "qr_tag" in tags and re.search(r"<QR:[^>]+>", text):
                    if index > 0:
                        print("QRコードの前に改行を追加")
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # QRコードの処理
                    qr_content = re.search(r"<QR:([^>]+)>", text).group(1)
                    commands.append(("qr", qr_content, {}))
                    is_text = False  # QRコードはテキストではない

                # ITFコード
                if "itf_tag" in tags and re.search(r"<ITF:[^>]+>", text):
                    if index > 0:
                        print("ITFコードの前に改行を追加")
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # ITFコードの処理
                    itf_content = re.search(r"<ITF:([^>]+)>", text).group(1)
                    commands.append(("itf", itf_content, {}))
                    is_text = False  # ITFコードはテキストではない

                # EANコード
                if "ean_tag" in tags and re.search(r"<EAN13:[^>]+>", text):
                    if index > 0:
                        print("EANコードの前に改行を追加")
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # EANコードの処理
                    ean_content = re.search(r"<EAN13:([^>]+)>", text).group(1)
                    commands.append(("ean", ean_content, {}))
                    is_text = False

                # Code39コード
                if "c39_tag" in tags and re.search(r"<C39:[^>]+>", text):
                    if index > 0:
                        print("CODE39コードの前に改行を追加")
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # CODE39コードの処理
                    code39_content = re.search(r"<C39:([^>]+)>", text).group(1)
                    commands.append(("c39", code39_content, {}))
                    is_text = False  # CODE39コードはテキストではない

                # Code128コード
                if "b128_tag" in tags and re.search(r"<B128:[^>]+>", text):
                    if index > 0:
                        print("B128コードの前に改行を追加")
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # B128コードの処理
                    b128_content = re.search(r"<B128:([^>]+)>", text).group(1)
                    commands.append(("c128", b128_content, {}))
                    is_text = False  # B128コードはテキストではない

                # テキストのタグを解析してjptext2の引数を設定
                # 横倍角
                if "bold" in tags:
                    jptext2_args_dict["dw"] = True
                # 縦倍角
                if "vert" in tags:
                    jptext2_args_dict["dh"] = True
                # アンダーライン
                if "underline" in tags:
                    jptext2_args_dict["underline"] = True
                # 反転
                if "invert" in tags:
                    jptext2_args_dict["wbreverse"] = True
                # 4倍角
                if "four" in tags:
                    jptext2_args_dict["dw"] = True
                    jptext2_args_dict["dh"] = True

                #文字が存在しない場合はコマンド追加しない
                # テキストはTM88IVのjp2コマンドで送信
                if is_text:
                    commands.append(("jp2", text, jptext2_args_dict))
                #
                index += 1

            print("---")
            commands.append(("jp2", "\n", jptext2_args_dict))
    
        return commands