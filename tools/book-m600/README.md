# 第 600 号《AI大模型巴别塔的倒塌》出版工具链

由 `tools/book-m552/` 复制改写，版式照第 220、302 号（与 552 相同）。所有命令在**仓库根目录**运行；不含令牌；不做 git 操作。

## 本书参数（唯一来源 `meta.py`）

| 项 | 值 |
|---|---|
| 书号 / slug | 600 / `babel-tower-collapse` |
| 书名 | AI大模型巴别塔的倒塌 |
| 副题 | 统一性的最大赢家，成了同一性谱系的接生婆 |
| 题词 | 塔建成之日，就是塔倒之时。（署“——本书”） |
| 著者 | 王德生（无 advisor） |
| ISBN / 定价 | 979-8-90690-630-4 / US$25.00 |
| 版本 / 日期 / 版次 | V=20261106b / 2026-11-06 / 2026 年 11 月第 1 版 |
| 分类 CATEGORY | `core`（见“待决事项”） |
| tier | L0；tier_reason：主张层为主——命题、判据、三塔三尺、暂定九格读法；陪读场景为构想；无真跑数据 |
| UNIT_REV | 20261106-m600-unit-v1 |
| 智能体名 | 接生婆（占位；文案另写） |
| 体量 | 理论专著约 30 万字（定稿实计正文约 28.9 万汉字（含前言、导读、附录）） |

## 结构

序章（导论位置，正文页码从序章起为 1）；第一编（1–5 章）、第二编（6–10 章）、第三编（11–14 章）、第四编（15–16 章）；结语；
前言、导读、附录一至四、参考书目**暂缺**，缺了自动跳过，由别人另写后放进 `src/full.raw.md` 即可（标题格式 `# 前言　…`、`# 导读　…`、`# 附录一　…`、`# 参考书目`）。

编名在稿里写“上编／中编／下编／终编”，convert 统一成“第一编…第四编”并插编序；编的归属**按章号**（`convert.py` 的 `PARTS`），不按稿里编题的位置。

## 与 552 的差异

- 十六章、四编（上 1–5、中 6–10、下 11–14、终 15–16），552 是十四章；`NCH = 16`。
- 有序章（`front/01-导言.md`，`build.py` 的 LUN 机制，kind=main）；552 没有导论。
- 章末是“带走的话”＋“这一章怎样算错”，没有“小账”。后者在 `build.py` 的 `quote_html` 里与小账同版式（`.ledger`），标签为“这一章怎样算错”；孤页检测与“章末绑定防拆页”都已认它。
- 章末块的两种写法（`## 带走的话` 标题式、`**带走的话**` 整行加粗式，中间可夹 `---`）都认。
- 节题认 `## N.M 题` 与 `## 序.M 题`。
- 前言、导读、附录、参考书目可缺（552 缺了会报错）；参考书目在后置里排在附录之后、版本说明之前（`build.py` 认“参考书目”为书目体例）。
- 稿末附注只切明确尾标（`〔待核〕清单`、`附：`、`稿末附件／附录`、`自数字数`、`字数自数`），不再切裸“待核”。
- 封面：三层塔（青、金、奶白三种纯色块）中部一道斜裂缝，塔脚下一只小手托起发芽的种子，身后五层金色光环；无小字行；书名两行，副题金色。封底：判词五行、简介一段、金句、出版信息三行、EAN-13 与 US$25.00。全部纯色，无渐变。
- `front/00-前置.tpl.md`（出版信息、题词、作者介绍、成书说明）、`back/12-后置.tpl.md`（版本说明）已按本书改写，其中成书说明与版本说明是**占位稿**，需王德生或统稿人确认。
- `INTRO`（四编编序）是每编 3–4 句的占位稿。

## 已改动点（相对复制来的 552 文件）

`meta.py`、`convert.py`（重写）、`cover.py`（art、封面封底文字重写）、`build.py`（书名页、目录摘要、序章页眉、怎样算错版式、参考书目）、
`front/00-前置.tpl.md`、`back/12-后置.tpl.md`、`run_all.sh`、`publish.py`（授权文字）；`build_unit_600.py`、`gen_config.py`、`register.py`、`agent_page.py`、`make_docx.py` 只做改名（552→600、slug、路径）。
`content.json` 里只改了 `agent.name`（接生婆）与 `titleEn`，其余见下。

## 未完成点

- 本工具链 2026-11-06 由 537 目录改号重建（537 号被《AI接管秩序之后》占用）。定稿 `src/full.raw.md` 已含前言、导读、序章、十六章、结语、附录一至四，无〔待核〕标记；参考书目无（可缺）。
- `content.json` 来自 `content.new.json`（16 章学习任务）；`detail.html` 仍是 552 旧件，上站前须核对。
- 本地构建已验证（`/tmp/b600`），尚未跑 `--publish`；`publish.py` 的字数、章数口径上站前再核。

## 待决事项

1. CATEGORY：同系列里 545、551 是 `core`，543 是 `culture`，552 是 `math`；暂用 `core`。
2. 编的归属：测试稿里“下编”编题写在第 12 章前（第 11 章落在“中编”下）；按任务书改为下编 = 11–14 章。若定稿以稿里位置为准，改 `PARTS`。
3. 编名用“第一编…第四编”（任务书要求）；`build.py`、`build_unit_600.py` 同时认“上中下终”与“第X编”。

## 重跑

```bash
B=/tmp/b600; mkdir -p $B

# 新稿放到 tools/book-m600/src/full.raw.md 后：
bash tools/book-m600/run_all.sh $B          # convert → 封面 → 两版 PDF＋全文网页 → Word；不上站

# 逐步：
python3 tools/book-m600/convert.py
WAN=$(python3 -c "import json;print(round(json.load(open('tools/book-m600/han.json'))['body']/10000))") \
  python3 tools/book-m600/cover.py --fonts /usr/share/fonts/opentype/noto --out $B
python3 tools/book-m600/build.py --fonts /usr/share/fonts/opentype/noto --out $B      # 约 10–15 分钟
python3 tools/book-m600/make_docx.py --out $B

# content.json 重写、复核后才可：
bash tools/book-m600/run_all.sh $B --publish    # 会改 public/，不做 git
```

依赖：`pip install weasyprint pymupdf`，另需 pandoc、python-docx、poppler（pdftoppm/pdffonts）、Noto CJK 字体。
