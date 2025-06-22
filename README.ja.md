# MiniCapturePrint

## 概要
ご家庭にあるサーマルプリンタ（レシートプリンタ）で、メモや画像を手軽に印刷できるアプリです。（イメージは[キングジム](https://www.kingjim.co.jp/)さんの[ココドリ](https://www.kingjim.co.jp/sp/cc10/)風）
前プロジェクト（[WPT](https://github.com/hatotank/WPT)）の応用のため、絵文字も印刷可能です。
※EPSON TM-T88IV（有線LANモデル）で開発・動作確認をしています。他のプリンタではソースコードの一部改造が必要な場合があります。

![アプリメインフォーム](/images/img001.png)
![印刷サンプル](/images/img002.png)

## インストールと起動

**1. インストール**

以下のコマンドでサブモジュールを含めてダウンロードします。

```
git clone --recurse-submodules https://github.com/hatotank/MiniCapturePrint.git
```

**2. 起動**

フォルダ内の`luncher.pyw`をダブルクリックして起動します。

**補足**

サブモジュール（https://github.com/hatotank/tm88iv）を使用しているため、通常の`git clone`だけではすべてダウンロードされません。上記のコマンドでクローンした場合は、以下のコマンドでサブモジュールを取得してください。

```
git submodule update --init --recursive
```

## 制限

漢字コマンドを使用しているため、サーマルプリンタは基本的に日本語モデル限定です。

## 使い方

`luncher.pyw`を起動すると、フォントとJISデータがダウンロードされます。
※2回目以降の起動時は、ファイルの存在をチェックし、存在しないファイルのみ取得します。

![ダウンロードツール](/images/img003.png)

**ダウンロード先**
- NotoSansJP-Medium.otf  
  https://github.com/notofonts/noto-cjk/releases/download/Sans2.004/16_NotoSansJP.zip
- OpenMoji-black-glyf.ttf  
  https://github.com/hfg-gmuend/openmoji/releases/download/15.1.0/openmoji-font.zip
- unifont_jp-16.0.03.otf  
  https://unifoundry.com/pub/unifont/unifont-16.0.03/font-builds/unifont_jp-16.0.03.otf
- JIS0201.TXT  
  http://unicode.org/Public/MAPPINGS/OBSOLETE/EASTASIA/JIS/JIS0201.TXT
- JIS0208.TXT  
  http://unicode.org/Public/MAPPINGS/OBSOLETE/EASTASIA/JIS/JIS0208.TXT
- JIS0212.TXT  
  http://unicode.org/Public/MAPPINGS/OBSOLETE/EASTASIA/JIS/JIS0212.TXT
- JIS0213-2004.TXT  
  https://raw.githubusercontent.com/hatotank/WPT/refs/heads/main/JIS0213-2004.TXT

**起動後のメインフォーム（左側）**
文字装飾は視覚的に反映されます。バーコードは入力プロンプトで入力します。
※文字の位置揃えは制御のみで印刷されませんので、画面上の行番号と印字行数は一致しません。

![メインフォーム左のテキストエリア](/images/img004.png)

**起動後のメインフォーム（右側）**
ファイルの読み込みは、基本的にドラッグ＆ドロップのみ対応しています。

![メインフォーム右の画像エリア](/images/img005.png)

**設定画面（設定・ハイブリッド詳細設定）**
![設定画面](/images/img006.png)

**その他の画面**
![その他画面](/images/img007.png)

## ライセンス

MIT

## 作者

[hatotank](https://github.com/hatotank)

## 参考

TM-T88IV  
https://www.epson.jp/support/portal/support_menu/tmt884e531.htm

TECH.REFERENCE  
https://download4.epson.biz/sec_pubs/pos/reference_ja/

## ディザ処理の印刷サンプル（一部）
![ディザ処理の印刷サンプル](/images/img008.png)
