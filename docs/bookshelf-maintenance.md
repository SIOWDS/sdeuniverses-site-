# 统一专著书架

书籍目录的唯一数据源是 `public/books/catalog.json`。`/books/`、`/monographs/` 和读书馆的 `/library/` 由同一份数据生成，避免数量和书目各自漂移。

新增或修改图书时，先维护目录中的稳定 `id`、书名、作者、主题、简介、主书页、阅读方式、阅读链接、可选PDF及封面，再运行：

```sh
python3 tools/build_bookshelf.py
```

将JSON与三个生成的HTML一起提交。没有完整书号不影响作为在线作品收录，但不能因此标记为已正式出版。书架显示的是独立图书数，而不是出版登记确认数。

`readMode` 只描述阅读资源：`full` 为全文入口（网页或完整PDF）；`preview` 为明确的试读版；`info` 为只有介绍/导读。只能链接现有资源；不把内容介绍标成全文。PDF链接只保留作者原来已提供的入口，尊重仅限在线阅读的作品。不同版本、导读页和子站镜像应归入同一个书目。

样式和交互分别在 `public/books/bookshelf.css` 与 `bookshelf.js`。全部卡片和链接预先写入HTML，JavaScript只增强搜索、筛选、排序与分批展示；关闭JavaScript仍能浏览全部图书。无需新服务、数据库或密钥。

本次书目清洁仅整理展示与阅读入口，不擅自改动书号登记。两组已发现的异书同ISBN仍需对照出版社台账处理。

翻页阅读和章节阅读是不同入口。现有翻页器记录为 `flipUrl`，并始终作为 `readUrl` 主按钮，全文标「在线翻页阅读」，试读标「在线翻页试读」。网页版目录另存 `chapterUrl`，显示「章节阅读」。不要用章节目录或直接PDF替换现有翻页器；未有翻页器的书不得仅改标签冒充翻页。阅读筛选中的「在线翻页」涵盖全文和明确标注的试读版。

有全文但尚无翻页器的图书：在目录填写 `reader: {format: "pdf" | "html", sources: [{title, url}]}`，再运行 `python3 tools/build_book_readers.py` 和 `python3 tools/build_bookshelf.py`。PDF源按原始版面翻页；HTML源必须逐章按既有目录顺序列全，阅读器按屏幕分页并连续跨章阅读。新书发布时必须同时检查翻页器、书架主入口和书籍详情入口。只有介绍、尚未核实完整正文的书不能标为全文。

---

# 追记 · 2026-09-19 的一次全面核查

上面那份规程讲的是**怎么做**；这一段记的是**做完之后怎么核**，以及这次核出来的四件事。

## 一、这次修了什么

| 处 | 病 | 因 |
|---|---|---|
| `m/84`、`m/92` 的 `read.html` | **翻页阅读打得开、但一页也渲染不出** | 学员 PDF 迁 R2 时（`721c93a3`），`PDF_URL` 仍指 `/students/chen-xiaoyan/…`，404。PDF 实际一直在 `/books/m/84/`、`/books/m/92/` 下 |
| `m/80`、`m/81`、`m/82`、`m/84`、`m/92` | 中文文件名的 PDF 路径未编码 | 一直靠浏览器自动编码兜着，换环境就可能断。五处统一包 `encodeURI(...)` |
| `m/100`、`m/93`、`m/98`、`m/99`、`m/121`、`m/122` 书目页 | 封面图引用丢失（文件在、页面不引用） | 用脚本重生成书目页时冲掉了后期手加的 `<img>` |
| `bookshelf.css`、`reader/reader.css` | 与全站不是一副面孔 | 书架与新阅读器是浅色，全站是深墨底金线。两处各追加一段**墨金覆盖层**，未改原规则；**回退＝删掉文件末尾那一段** |

## 二、这一类病的共同形状（值得记住的那一条）

**页面能打开 ≠ 内容取得到。**

`m/84` 与 `m/92` 在任何"链接可达性"检查里都是 200——坏的是 `read.html` 里那行 `PDF_URL`。
**凡涉及阅读器，必须跑到渲染那一步才算核过。**

## 三、核查办法：跑脚本

```sh
python3 tools/check_bookshelf.py            # 本地静态四道（秒级）
python3 tools/check_bookshelf.py --online   # 加线上可达性（分钟级）
python3 tools/check_bookshelf.py --render   # 加渲染真跑（要 playwright，最慢也最硬）
```

**不通过时退出码为 1**，可以直接挂进发布前的检查。

五道分别是：① catalog 与本地文件一致性　② 书目页封面引用　③ 老阅读器的 `PDF_URL`（存在性／中文未编码／迁移未跟改，`/students/` 的会去 R2 真取一次）　④ 书架静态资源是否写死绝对地址　⑤ 线上可达性（跟随跳转）　⑥ `--render` 时加阅读器渲染真跑。

**这个脚本是拿 2026-09-19 那次的病验过的**：把 `m/84` 的 `PDF_URL` 改回迁移前的旧路径，③ 会同时报出「R2 取不到（404）」与「中文路径未 encodeURI」，退出码 1。

下面是各道背后的原始命令，脚本坏了或要临时手查时用：

```sh
# ① catalog 与本地文件一致性（秒级）
#    逐条查 detailUrl/readUrl/chapterUrl/pdfUrl/coverUrl 在本地是否存在
#    注意：/students/**.pdf 本地不存在是正常的，它们走 R2，见 docs/pdf-storage-scope.md

# ② 线上可达性（分钟级）——必须带 -L，站内有大量 301/307
curl -s -L -o /dev/null -w '%{http_code}' <url>
#    307：read.html → read（去扩展名）；301：部分书跳去 lang. 等子站。两者都不是坏

# ③ 老阅读器的 PDF 源（秒级）
grep -o 'PDF_URL = [^;]*' public/books/m/*/read.html
#    看三件：文件存不存在、是否中文名未编码、是否还指着已迁走的 /students/ 路径

# ④ 渲染真跑（唯一能抓住 84/92 那类病的）
#    用浏览器打开 read.html，等 4 秒，检查：
#      - 是否出现「载入失败 / 未能载入」
#      - document.querySelector('canvas') 是否有非零尺寸
#      - 页码总数是否与书的实际页数相符
```

**本次读数：128 条 × 5 个入口线上全量扫描，异常 0；84/92/121 三本渲染真跑通过（343 / 224 / 383 页）。**

## 四、三条留给下一次的

1. **改书目页别用整页重生成。** 书目页常有后期手加的内容（封面、结构段、特殊说明），脚本重生成会静默冲掉。要改就定点插改，改完 `grep cover.jpg` 核一遍。
2. **CSS/JS 引用用站内绝对路径 `/books/…`，不要写 `https://sdeuniverses.com/…`。** 后者会让本地预览加载线上文件，改了看不见效果，容易误判"没生效"。
3. **迁移任何 PDF 之后，必须回头 grep 一遍谁在引用它。** 这次 `721c93a3` 迁了 18 个文件，书目页的链接改了，`read.html` 里的 `PDF_URL` 没改——而后者才是阅读器真正用的那个。

---

# 追记 · 2026-09-24　翻页阅读器的「矢量」模式曾全站静默失效

**病**：翻页阅读器默认用 PDF.js 的 SVGGraphics 做矢量渲染，但 `getDocument` 没开 `fontExtraProperties`。
只要 PDF 里嵌了字体（几乎所有书都嵌了），SVGGraphics 一执行 `setFont` 就抛
`addFontStyle: No font data available`，阅读器随即**不提示地**退回位图，右上角按钮从「矢量」变成「位图」。
页面 200、PDF 200、翻页正常——所有可达性检查都看不出来。

**修**：41 个带 SVGGraphics 的阅读器统一为
`pdfjsLib.getDocument({url:CFG.pdf, rangeChunkSize:262144, fontExtraProperties:true})`（后来又补一个参数，见下）
（其中 167、173、178、188、192 已先由各自的发书提交修好，本次补齐其余 35 个）。

**新书纪律**：复制阅读器时照抄这一行；发布后用无头浏览器打开 `read.html`，等 10 秒，
读 `#btnVec` 的文字——是「矢量」才算过，是「位图」就回来查。
**第二个病（同日查出）**：只开 `fontExtraProperties` 还不够。凡 PDF 里有位图（多数书的封面、封底是贴图），
PDF.js 3.11 默认用 OffscreenCanvas 把图片解成 ImageBitmap，`imgData.data` 为空，SVGGraphics 读图时抛
`Cannot read properties of null (reading 'subarray')`，同样静默退回位图——实测 42 个阅读器里有 33 个是这样。
所以现行这一行是：
`pdfjsLib.getDocument({url:CFG.pdf, rangeChunkSize:262144, fontExtraProperties:true, isOffscreenCanvasSupported:false})`
两个参数缺一不可。两个都开了仍退回位图的，才是 PDF 本身含 SVGGraphics 不支持的东西，要改 PDF，不是改阅读器。

---

# 追记 · 2026-09-24（三）　全部翻页阅读器统一为矢量渲染（旧式位图阅读器整批迁移）

**结果**：专著书架下凡是 PDF 源的翻页阅读器，全部走 PDF.js SVGGraphics 矢量渲染，`getDocument` 一律带
`fontExtraProperties:true, isOffscreenCanvasSupported:false`。

| 类 | 数 | 做法 |
|---|---|---|
| 旧式位图阅读器（`PDF_URL` 那一种） | 66 | `tools/build_flip_reader.py migrate` 整批迁到矢量模板；目录从 PDF 书签生成（书签过细时只留第一层；没有书签的书，浏览器端再兜一次）；页码按物理页（offset 1）；**保留 WDS 陪读**（`WDS_READ` ＋ wds-read.js / wds-mode.js） |
| 手写矢量阅读器 | 43 | 加**逐页回退**（188、192 原本就是）：某页画不了矢量只那一页用高清位图，其余页照旧矢量；连续失败 6 页以上且失败多于成功，才整本切位图 |
| 共享 `books/reader/reader.js`（19 本 PDF 源＋10 本 HTML 源） | 1 个文件 | 加矢量渲染＋逐页回退，两个参数照抄；版本号升 `20260924-reader-v3` |
| `lion-city-glory` | 1 | 自有版式，未动，单独维护 |

**模板与生成器**：模板 `tools/flip_reader_template.html`（`tools/book_read_template.html` 与它相同）；
生成器 `tools/build_flip_reader.py`：`one`（新书）、`migrate`（旧阅读器整批迁移）。

**一个差点出事的坑**：`tools/build_book_readers.py` 会按 catalog 里的 `reader` 字段重建阅读器，
m/34、130、133 在 catalog 里也有 `reader` 字段——一跑就把它们的手写矢量阅读器冲回 reader.js 位图版。
已加保护：**已存在且含 SVGGraphics 的阅读器不再被覆盖**。

**体检**：`tools/check_bookshelf.py` 新增第 ⑦ 道——PDF 源阅读器缺 SVGGraphics、缺两个参数之一，即报错。

---

# 追记 · 2026-09-24（四）　第三个参数组：CMap 与标准字体；狮城荣耀并入矢量

**病**：两个参数都开了，m/49 仍有页面退回位图，控制台报
`The CMap "baseUrl" parameter must be specified, ensure that the "cMapUrl" and "cMapPacked" API parameters are provided`。
用预置 CMap（如 UniGB-UCS2-H）编码的 CJK 字体、以及没嵌入的 14 种标准字体，PDF.js 要去取 CMap／标准字体文件；不给地址就解析失败，
那一页退回位图，严重时缺字。

**修**：全部 PDF 源阅读器（112 个 read.html、共享 reader.js、模板）的 `getDocument` 再加
`cMapUrl:'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/', cMapPacked:true, standardFontDataUrl:'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/standard_fonts/'`。
**注意用 jsdelivr，不用 cdnjs**：cdnjs 的 pdf.js 3.11.174 只放了 pdf.min.js，`/cmaps/`、`/standard_fonts/` 一律 403（实测）。

`lion-city-glory` 的自有版式阅读器保留原样式，只把渲染换成 SVGGraphics＋逐页回退，并补齐四组参数。

`check_bookshelf.py` 第 ⑦ 道增加 `cMapUrl` 检查。
