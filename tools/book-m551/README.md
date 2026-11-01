# 第 551 号《AI时代的职业教育出路：技术的同一性谱系》出版工具链

副题：基于SDE技术发生智能体的路径同一性发生学　王德生 著　ISBN 979-8-90690-553-6　US$20.00　V=20261101b　tier L0。
由第 549 号工具链改写，版式照第 220、302 号。所有命令在**仓库根目录**运行；不含任何令牌；不做 git 操作。

## 文件

| 文件 | 作用 |
|---|---|
| `meta.py` | 书号、书名、ISBN、定价、版本、题词、tier 的唯一来源 |
| `synth_full.py` | 把 `/home/claude/551-jishu-tongyixing-puxi/chapters/` 合成 `src/full.md`，并收集〔待核〕到 `待核总表.md`（临时合成器；统稿人另行合成时可不用） |
| `convert.py` | 读 `src/full.md`，写 `front/00-前置.md`、`parts/01–08.md`、`back/12-后置.md`、`book.md`、`han.json` |
| `cover.py` | 封面封底（六路径与地板图；藏青墨绿底） |
| `build.py` | 两版 PDF（印刷 170×240、阅读 190×250）＋全文网页 |
| `make_docx.py` | 全书 Word（pandoc） |
| `publish.py` | 装进 `public/books/m/551/`、书目、站点地图、/today/ 新书卡、书号预留档 |
| `gen_config.py` + `build_unit_551.py` | 学习包（36 个单元）与出版单元 |
| `register.py` / `agent_page.py` | 登记智能体「鞋带」、keypoints、智能体页 |
| `content.json` | 智能体、学习任务、承重命题、要点等文案（质检后须对照新稿复核） |
| `run_all.sh` | 一键串起来 |

## `src/full.md` 的格式（convert.py 认的）

- 一级标题：`# 前言　题`、`# 导读　题`、`# 第一编　题`……`# 第八编　题`、`# 第N章　题`（1–36）、`# 结语　题`、`# 附录一　题`……`# 附录四　题`。标题与题之间空格或全角空格均可。文件第一行可有书名一级标题，会被忽略。
- 章内节：`## N.M 题`；节内小标题：`### 题`。前言、导读、结语、附录里的 `## 一、……` 也算节。
- 章末的“这一章的问题”“带走的话”“小账”各种写法（加粗位置、冒号位置、小账一／二、第一行／第二行、列表、一二三）convert.py 会统一改成引用块；围栏代码块原样保留。
- 稿末附注（〔待核〕清单、新造案例清单、自数字数、交稿说明）必须切掉。切法：以首个匹配 `^(#+ ?|\*\*)?(〔待核〕清单|附：|待核)` 的行为界；synth_full.py 另补了 `稿末附件／稿末附录`、`**字数／自数字数／自查表／本稿新造／拿不准／建议`、`字数自数／自数：` 等同类尾标。

## 用质检后的稿一键重跑

```bash
B=/tmp/b551            # 构建输出目录，随便选
mkdir -p $B

# 1 合成：有统稿人合成稿就直接放到 tools/book-m551/src/full.md；否则用临时合成器
python3 tools/book-m551/synth_full.py          # 同时重写 待核总表.md

# 2 只做本地构建（不上站）：convert → 封面 → 两版 PDF＋全文网页 → Word
bash tools/book-m551/run_all.sh $B

# 3 复核 content.json 与新稿是否还对得上（章标题、节名、预言编号、年份、字数口径），再改 content.json

# 4 上站（会改 public/，请先确认；仍不做 git）
bash tools/book-m551/run_all.sh $B --publish
```

`--publish` 展开后的命令顺序（与第 545 号 run_all.sh 一致）：

1. `python3 tools/book-m551/convert.py`
2. `WAN=<字数/万> python3 tools/book-m551/cover.py --fonts /usr/share/fonts/opentype/noto --out $B`
3. `python3 tools/book-m551/build.py --fonts /usr/share/fonts/opentype/noto --out $B`（印刷版、阅读版、text.html；约 10 分钟）
4. `python3 tools/book-m551/make_docx.py --out $B`
5. `python3 tools/book-m551/publish.py --build $B --content tools/book-m551/content.json --ms tools/book-m551/book.md`
6. `python3 tools/book-m551/gen_config.py tools/book-m551/content.json`（写 `tools/book_unit/m551.json`）
7. `python3 tools/book-m551/build_unit_551.py --config tools/book_unit/m551.json --out-pdf public/books/m/551/learning-pack.pdf`
8. `python3 tools/book-m551/register.py`、`python3 tools/book-m551/agent_page.py`
9. `python3 tools/build_bookshelf.py --shelf-only`、`python3 tools/build_book_rag.py 551`

注意：build_unit 要读 publish 放进 `public/books/m/551/text/index.html` 的章锚点，所以 publish 必须先于 build_unit（顺序不能照“build→register→gen_config→build_unit→publish”走）。publish 会查书号与 ISBN 重复，并写 `.publish/volume-reservations/551.json`。

## 重跑前要核对的几件事

- `待核总表.md`：质检后稿里的〔待核〕标记与清单若有变，重跑 synth_full.py 更新。
- `content.json`：tasks 的“失败条件”和 keypoints、loadBearing 是据当时稿写的，章名、节名、预言编号与年份以质检后稿为准。
- `convert.py` 里的 `INTRO`（八编编序）、`front/00-前置.tpl.md`（成书说明）、`back/12-后置.tpl.md`（版本说明）里的待裁定事项，裁定后同步改。
- 书中“SDE技术发生智能体”及其算法、162/4,374 谱位、十二条预言都是设想，所有对外文案（含智能体与学习包）须保持这个口径。
