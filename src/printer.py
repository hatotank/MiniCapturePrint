import re
import logging
from tm88iv.tm88iv import TM88IV

class PrinterHandler:
    """
    プリンタを操作するクラス
    """
    def __init__(self, ip_address, media_width=512, config=None):
        """
        プリンタの初期化

        :param ip_address: プリンタのIPアドレス
        :param media_width: メディアの幅（ピクセル単位）
        :param config: 設定オブジェクト（オプション）
        """
        # プリンタの初期化
        self.tm_print = TM88IV(ip_address, config=config) 
        # プリンタのメディア幅を設定(python-escpos ver3.1にて確認
        self.tm_print.profile.profile_data['media']['width']['pixels'] = media_width

        # ログ設定
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # デバッグ時 INFO --> DEBUG

    def print_text_with_tags(self, text_widget, image_path=None, enable_text_print=False, enable_image_print=False, should_cut_paper=False):
        """
        タグ付きテキストを印刷します。

        :param text_widget: タグ付きテキストを含むウィジェット
        :param image_path: 印刷する画像のパス
        :param enable_text_print: テキスト印刷を有効にするかどうか
        :param enable_image_print: 画像印刷を有効にするかどうか
        :param should_cut_paper: 印刷後に用紙をカットするかどうか
        """
        # 印刷有効フラグ
        debug_print_enabled = True # デバッグ用の印刷フラグ
        # 印刷フラグ
        isprinted = False
        # タグ解析
        parser = TextTagParser(text_widget)
        commands = parser.parse()
        self.logger.debug(f"=== タグ解析結果 ===")
        self.logger.debug(f"コマンド: {commands}")

        # テキストが含まれているかどうか
        text_included = False  
        if any(cmd[0] in ("jp2", "qr", "itf", "ean", "c39", "c128") for cmd in commands):
            text_included = True

        if debug_print_enabled:
            self.logger.debug(f"=== 印刷開始 ===")
            self.logger.debug(f"テキスト印刷: {enable_text_print}, 画像印刷: {enable_image_print}, 用紙カット: {should_cut_paper}")
            self.logger.debug(f"テキスト含むか: {text_included}")
            self.logger.debug(f"画像パス: {image_path if image_path else 'なし'}")

            # プリンタを開く
            self.tm_print.open()

            if enable_text_print and text_included:
                for arg_type, arg_command, arg_dict in commands:
                    self.logger.debug(f"コマンド: {arg_type}, 引数: {arg_command}, オプション: {arg_dict}")
                    # 絵文字対応日本語出力
                    if arg_type == "jp2":
                        self.tm_print.jptext2(arg_command, **arg_dict)
                        isprinted = True  # 印刷フラグを設定
                    # バーコード：QRコード
                    if arg_type == "qr":
                        self.tm_print.qr(arg_command, native=True)
                        isprinted = True  # 印刷フラグを設定
                    # バーコード：ITFコード
                    if arg_type == "itf":
                        self.tm_print.barcode(arg_command, bc="ITF", align_ct=False, width=2)
                        isprinted = True  # 印刷フラグを設定
                    # バーコード：EANコード
                    if arg_type == "ean":
                        self.tm_print.barcode(arg_command, bc="EAN13", align_ct=False, width=2)
                        isprinted = True  # 印刷フラグを設定
                    # バーコード：Code39コード
                    if arg_type == "c39":
                        self.tm_print.barcode(arg_command, bc="CODE39", align_ct=False, width=2)
                        isprinted = True  # 印刷フラグを設定
                    # バーコード：Code128コード
                    if arg_type == "c128":
                        # CODE128は(SHIFT or CODE A or CODE B or CODE C)の内、CODE Bを使用
                        self.tm_print.barcode("{B" + arg_command, bc="CODE128", align_ct=False, function_type="B", width=2)
                        isprinted = True  # 印刷フラグを設定
                    # 他のコマンド
                    if arg_type == "row":
                        self.tm_print._raw(arg_command)

            if enable_image_print and image_path:
                self.logger.debug(f"画像を印刷: {image_path}")
                self.tm_print.image(image_path, center=False)
                isprinted = True  # 画像印刷フラグを設定

            if isprinted and should_cut_paper:
                self.logger.debug("用紙をカットします")
                self.tm_print.cut()  # カットコマンドを送信

            self.logger.debug("=== 印刷完了 ===")

            # プリンタを閉じる
            self.tm_print.close()


class TextTagParser:
    """
    タグ付きテキストを解析し、TM88IVのエスケープコマンドに変換するクラス
    """
    def __init__(self, text_widget):
        """
        タグ付きテキストを解析するクラスの初期化

        :param text_widget: タグ付きテキストを含むウィジェット
        """
        self.text_widget = text_widget
        self.esc_commands = []  # 最終的にPrinterHandlerへ渡すコマンド列
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # デバッグ時 INFO --> DEBUG

    def parse(self):
        """
        タグ付きテキストを解析し、TM88IVのエスケープコマンドに変換する

        :return: エスケープコマンドのリスト
        """
        # 既存のコマンドをクリア
        self.esc_commands.clear()
        # 各行のタグブロックを取得
        self.blocks_per_line = self._get_line_tag_blocks()
        # タグブロックをESC/POSコマンドに変換
        self.esc_commands = self._convert_line_to_esc()
        # 変換結果を返す
        return self.esc_commands

    def _get_line_tag_blocks(self):
        """
        各行のタグブロックを取得（改行もセグメントとして含める）
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
            # 行末に改行があれば追加
            if lineno < total_lines or self.text_widget.get(line_end) == '\n':
                tags = self.text_widget.tag_names(line_end)
                segments.append(('\n', tags))
            # タグセットごとにブロック圧縮
            compressed = self._compress_tagged_segments(segments)
            results.append(compressed)
        return results

    def _compress_tagged_segments(self, segments):
        """
        タグ付きセグメントを圧縮する（改行も含めて圧縮）
        連続する同じタグの文字列を1つにまとめる

        :param segments: (文字, タグ)のリスト
        :return: 圧縮された(文字, タグ)のリスト
        """
        if not segments:
            return []

        compressed = []
        current_text = segments[0][0]
        current_tags = segments[0][1]

        for char, tags in segments[1:]:
            # 改行は常に新しいセグメントとして扱う
            if char == '\n':
                compressed.append((current_text, current_tags))
                compressed.append(('\n', tags))
                current_text = ''
                current_tags = None
                continue
            if tags == current_tags:
                current_text += char
            else:
                compressed.append((current_text, current_tags))
                current_text = char
                current_tags = tags
        if current_text:
            compressed.append((current_text, current_tags))
        return compressed

    def _convert_line_to_esc(self):
        """
        各行のタグブロックをTM88IVのエスケープコマンドに変換
        :return: エスケープコマンドのリスト
        """
        # エスケープコマンドのリスト
        commands = []
        #
        line_count = len(self.blocks_per_line)
        self.logger.debug(f"====")
        self.logger.debug(f"行数: {line_count}")

        # 初期位置は左
        commands.append(("row", b"\x1b\x61\x00", {}))
        for line_blocks in self.blocks_per_line:
            self.logger.debug(f"行ブロック: {line_blocks}")
            # 各行のテキストとタグを取得
            index = 0  # 行のインデックス
            include_text = False  # テキストが存在するかどうかのフラグ
            include_align = False  # 左寄せ、中央寄せ、右寄せのフラグ
            include_barcode = False  # バーコードが存在するかどうかのフラグ
            jptext2_args_dict = {"bflg": True}
            for text, tags in line_blocks:
                is_text = True  # テキストかどうかのフラグ
                jptext2_args_dict = {"bflg": True}

                # 左寄せ、中央寄せ、右寄せ
                if "align_left" in tags and re.search(r"<ALIGN:LEFT>", text):
                    commands.append(("row", b"\x1b\x61\x00", {}))
                    is_text = False
                    include_align = True
                if "align_center" in tags and re.search(r"<ALIGN:CENTER>", text):
                    commands.append(("row", b"\x1b\x61\x01", {}))
                    is_text = False
                    include_align = True
                if "align_right" in tags and re.search(r"<ALIGN:RIGHT>", text):
                    commands.append(("row", b"\x1b\x61\x02", {}))
                    is_text = False
                    include_align = True
                # 水平線
                if re.search(r"<HR>", text):
                    commands.append(("row", b"\x1b\x61\x00", {}))
                    commands.append(("jp2", "─────────────────────", jptext2_args_dict))
                    commands.append(("jp2", "\n", jptext2_args_dict))
                    is_text = False

                # バーコード：QRコード
                if "qr_tag" in tags and re.search(r"<QR:[^>]+>", text):
                    if index > 0:
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # QRコードの処理
                    qr_content = re.search(r"<QR:([^>]+)>", text).group(1)
                    commands.append(("qr", qr_content, {}))
                    is_text = False  # QRコードはテキストではない
                    include_barcode = True

                # バーコード：ITFコード
                if "itf_tag" in tags and re.search(r"<ITF:[^>]+>", text):
                    if index > 0:
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # ITFコードの処理
                    itf_content = re.search(r"<ITF:([^>]+)>", text).group(1)
                    commands.append(("itf", itf_content, {}))
                    is_text = False  # ITFコードはテキストではない
                    include_barcode = True

                # バーコード：EANコード
                if "ean_tag" in tags and re.search(r"<EAN13:[^>]+>", text):
                    if index > 0:
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # EANコードの処理
                    ean_content = re.search(r"<EAN13:([^>]+)>", text).group(1)
                    commands.append(("ean", ean_content, {}))
                    is_text = False  # EANコードはテキストではない
                    include_barcode = True

                # バーコード：Code39コード
                if "c39_tag" in tags and re.search(r"<C39:[^>]+>", text):
                    if index > 0:
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # CODE39コードの処理
                    code39_content = re.search(r"<C39:([^>]+)>", text).group(1)
                    commands.append(("c39", code39_content, {}))
                    is_text = False  # CODE39コードはテキストではない
                    include_barcode = True

                # バーコード：Code128コード
                if "b128_tag" in tags and re.search(r"<B128:[^>]+>", text):
                    if index > 0:
                        commands.append(("jp2", "\n", jptext2_args_dict))
                    # B128コードの処理
                    b128_content = re.search(r"<B128:([^>]+)>", text).group(1)
                    commands.append(("c128", b128_content, {}))
                    is_text = False  # B128コードはテキストではない
                    include_barcode = True

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

                if text == "\n":
                    # 改行の場合はコマンド追加しない
                    is_text = False

                # 文字が存在しない場合はコマンド追加しない
                # テキストはTM88IVのjp2コマンドで送信
                if is_text:
                    commands.append(("jp2", text, jptext2_args_dict))
                    include_text = True  # テキストが存在するフラグを設定

                # 行のインデックスを更新
                index += 1

            # 行の終わりに改行を追加
            if include_text or \
                (index == 1 and not include_barcode and not include_align and line_count > 1) or \
                (line_count == 1 and not include_barcode and include_align):
                commands.append(("jp2", "\n", jptext2_args_dict))
    
        return commands