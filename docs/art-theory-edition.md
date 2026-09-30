# SDE艺术论 · 2026年9月修订版

现有书目 ID 为 `art-theory`，沿用 `/books/art-theory/`，不另建重复书目。

本次修订保留三部三十二章，压缩重复论述，澄清SDE概念的适用范围，校正美学史与作品背景，补充术语对照、分析步骤及47项参考资料。网页全文和PDF使用同一份修订正文。

## 文件与入口

- 正文：`content/art-theory/revised-2026-09.json`
- 实际分页：`content/art-theory/page-map.json`
- 介绍：`public/books/art-theory/index.html`（手工版式，勿用通用详情页覆盖）
- 全文：`public/books/art-theory/chapters.html`
- 翻页：`public/books/art-theory/read.html`
- PDF：`public/books/art-theory/sde-art-theory-revised.pdf`

## 重新生成

使用Python 3、ReportLab、pypdf及Noto Serif SC字体的400、600字重静态TTF。字体采用Google Fonts的Noto Serif SC，遵循其SIL Open Font License；不把整份可变字体作为网站下载资产。

```bash
python3 tools/build_art_theory.py \
  --source content/art-theory/revised-2026-09.json \
  --out public/books/art-theory \
  --fonts /absolute/path/to/fonts
```

字体目录须包含 `NotoSerifSC-Regular.ttf` 和 `NotoSerifSC-Semibold.ttf`。

生成后将输出的 `page-map.json` 更新到 `content/art-theory/page-map.json`，并用 `tools/build_flip_reader.py` 生成本书翻页页。PDF封面为物理第1页，版权页开始标第1页，故 `--offset 2`。目录必须从本书最新PDF书签或实际分页表生成，不能复制其他书的目录。

```bash
python3 tools/build_flip_reader.py one \
  --read public/books/art-theory/read.html \
  --pdf /books/art-theory/sde-art-theory-revised.pdf \
  --title SDE艺术论 \
  --sub '幸福律与三号位发生 · 2026年9月修订版' \
  --detail /books/art-theory/ --offset 2 \
  --key art-theory-20260930-v1
python3 tools/build_bookshelf.py
```

出版日期沿用原书目，修订日期记入 `updatedAt`。全文状态为 `full`，主按钮进入翻页阅读，`chapterUrl` 指向全文阅读，PDF按钮指向上述实际文件。目录和PDF页码更新时须一起检查32章跳转，并重新核对介绍页中的页数。
