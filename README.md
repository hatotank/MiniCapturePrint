# MiniCapturePrint

## Overview
This is an application that allows you to easily print memos and images using a thermal printer (receipt printer) at home. You can easily print text, screenshots, and images. (Inspired by [King Jim](https://www.kingjim.co.jp/) [Cocodori](https://www.kingjim.co.jp/sp/cc10/))
Based on the previous project ([WPT](https://github.com/hatotank/WPT)), emoji printing is also supported.
*Developed and tested with EPSON TM-T88IV (wired LAN model). Some code modifications may be required for other printers.*

![Main Application Form](/images/img001.png)
![Print Sample](/images/img002.png)

## Installation and Startup

**1. Installation**

Clone the repository including submodules with the following command:

```
git clone --recurse-submodules https://github.com/hatotank/MiniCapturePrint.git
```

**2. Startup**

Double-click `luncher.pyw` in the folder to start the application.

**Note**

Since this project uses a submodule (https://github.com/hatotank/tm88iv), a simple `git clone` will not download all files. If you cloned with the above command, run the following command to fetch the submodule:

```
git submodule update --init --recursive
```

## Limitations

Because Kanji commands are used, this application is basically for Japanese model thermal printers only.

## Usage

When you start `luncher.pyw`, required fonts and JIS data will be downloaded automatically.
*From the second launch, only missing files will be downloaded.*

![Download Tool](/images/img003.png)

**Download Sources**
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

**Main Form (Left Side)**
Text decorations are visually reflected. Barcodes are entered via input prompts.
*Text alignment is only for display and does not affect the printed output, so the number of lines on screen and print may differ.*

![Text Area on Main Form (Left)](/images/img004.png)

**Main Form (Right Side)**
File loading is basically supported only by drag & drop.

![Image Area on Main Form (Right)](/images/img005.png)

**Settings Screens (Settings & Hybrid Details)**
![Settings Screen](/images/img006.png)

**Other Screens**
![Other Screens](/images/img007.png)

## License

MIT

## Author

[hatotank](https://github.com/hatotank)

## References

TM-T88IV  
https://www.epson.jp/support/portal/support_menu/tmt884e531.htm

TECH.REFERENCE  
https://download4.epson.biz/sec_pubs/pos/reference_ja/

## Dithering Print Sample (Partial)
![Dithering Print Sample](/images/img008.png)