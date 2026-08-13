# 专著第 80 号《判断的危机》构建链

沙盒会被清空，这三个脚本必须留在仓库里。

- `build_cover.py` — 纯 PIL 生成 cover.jpg（1240×1750）与 cover-full.jpg（封底＋书脊＋封面）。
  中文书脊必须逐字正立堆叠，整条横排 rotate(±90) 出来的汉字都是躺倒的。
  Noto CJK 字体 index=2 才是 SC，index=0 是 JP。
- `build_docx.py` — 由 `判断的危机.md` 生成 docx。版式 170×240mm、边距 17/15/16/15mm、
  正文 Noto Serif CJK SC 9.5pt / 行距 1.35 / 首行缩进 19pt，每页约 770 汉字。
  分页一律用 `paragraph_format.page_break_before`，不要用 add_break(WD_BREAK.PAGE)（会留空白页）。
  转 PDF：`soffice --headless --convert-to pdf`。
- `publish_80.py` — 生成 `public/books/m/80/text/` 下的分章网页与目录、出版信息页，
  并复制 PDF 与封面。read.html 若不存在则由第 78 号改写。

正文抽取只能走各篇 PDF（`pdftotext`）＋ HTML 里 `<a href="#sN">` 的目录标题切节；
直接解析文章页 HTML 会丢三分之一正文（各篇页面结构不统一）。
