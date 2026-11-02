# 第 474 号《AI时代的焦虑：主体性如何重生》出版工具链

王德生 著　ISBN 979-8-90690-557-4　US$50.00　V=20261102a　tier L0　分类 culture（文明与社会）　SLUG `ai-era-anxiety`。
由第 553 号工具链改写；版式照第 220、302 号（`build.py`）。所有命令在**仓库根目录**运行；不含任何令牌；不做 git 操作。

## 本书结构（「部—章—节」三层）

- 前置：出版信息、题词（判词）、作者介绍、前言、导读（罗马页码）；导论　先把几样工具磨一磨（阿拉伯页码起）。
- 正文四部四十章：第一部总纲（1–10）、第二部家长（11–20）、第三部职场（21–30）、第四部年轻人（31–40）。
  每部首页排部序（稿中【编序】两段）；每章：章首「本章 N 节：……」导语 → 「第一节　节题」（一级小标题）→ 「◆ 一、小节题」（二级小标题）；
  节末【带走的话】；章末【带走的话】＋【小账】＋【想一想】绑成一块不拆页。
- 后置：结语　错位、革命、重生；附录总页＋附录一至五；参考书目；后记。
- 规模：约 84 万字（含标点；取统稿元数据 `words`）；convert.py 另计正文汉字（前言、导读、导论、四十章、结语、附录，不计标题、表格、作者介绍、参考书目、后记）约 66.8 万，写入 `han.json`。出版信息页、详情页、/today/ 卡的“约 N 万字”都取 `han.json` 的 `wan`。

## 文件

| 文件 | 作用 |
|---|---|
| `meta.py` | 书号、书名、ISBN、**定价**、版本、判词、tier、分类、执笔说明的唯一来源；`COVER_DIR` 指向已定封面封底 |
| `src/full.md` | 统稿定稿的拷贝（run_all.sh 每次从 `/home/claude/book474/full.md` 复制；可用环境变量 `FULL_MD` 指别处） |
| `convert.py` | full.md → `front/00-前置.md`（出版信息由 meta 生成）、`front/01-导言.md`、`parts/01–04.md`、`back/12-后置.md`、`book.md`、`han.json` |
| `make_content.py` | 生成 `content.json`：智能体、详情页与书目文案为手写口径；承重命题（附录一十八条原话）、四十个学习单元、十八条要点从定稿抽取，定稿一改重跑即跟上 |
| `build.py` | 两版 PDF（印刷 170×240、阅读 190×250）＋全文网页 `text.html`（章锚点 `s\d+`）＋`toc-*.json`；封面封底取 `meta.COVER_DIR` 的 JPG，不画 |
| `make_docx.py` | 全书 Word（pandoc；部、章、节、◆ 为 1–4 级标题） |
| `publish.py` | 装进 `public/books/m/474/`、catalog、站点地图、/today/ 新书卡；在**已有**预留档 `.publish/volume-reservations/474.json` 上更新（保留原字段，原授权存为 `reservationAuthorization`） |
| `gen_config.py` + `build_unit_474.py` | 学习包（四十个单元，每章一个，按四部分组）与出版单元 |
| `register.py` / `agent_page.py` | 登记智能体「搭手」、keypoints、智能体页；名录卡放进本书书类分区（文明与社会） |
| `detail.html` | 详情页模板（书名、ISBN、定价、判词、执笔等全部由 publish.py 从 meta 填入） |
| `run_all.sh` | 一键串起来 |

## 一键重跑（定稿后）

```bash
B=/tmp/b474
bash tools/book-m474/run_all.sh $B              # 只做本地构建（拷定稿 → convert → content → 两版 PDF＋网页 → Word），约 1 小时
bash tools/book-m474/run_all.sh $B --publish    # 构建后上站各步（会改 public/；不做 git）
```

`--publish` 的顺序：publish → gen_config → build_unit_474 → register → agent_page → `build_bookshelf.py --shelf-only` → `build_book_rag.py 474`。
publish 必须先于 build_unit（build_unit 读 `public/books/m/474/text/index.html` 的章锚点）。
`build.py` 的逐章收紧行距结果缓存在 `/tmp/tight-<css哈希>.json`，正文不变的章重跑时不再试排。

## 改定价

只改 `meta.py` 的 `PRICE_USD` 一处，然后重跑 convert（出版信息页）、build（两版 PDF）、make_docx、publish（详情页、catalog、/today/、预留档）、gen_config＋build_unit（学习包封面页与 publication-unit.json）。
封底图上的「定价 US$50.00」印在 `/home/claude/book474/out/cover-back.jpg` 里，改价须由封面人重出封底。

## 分类

`culture`（文明与社会）。本书横跨家庭教育、职场、年轻人成长三处的社会性焦虑，主名是“主体性革命”这一文明层面的转变；站上同题邻卷第 241 号《我和我们》、第 386 号《隐私保护与“我”的诞生》在此类。`edu` 只覆盖第二部，`core` 偏 SDE 理论卷。要改，只改 `meta.CATEGORY`（agent_page 会跟着放到对应分区）。

## 口径守则（对外文案、智能体、学习包）

- 判词只用一句：焦虑和问题的诞生，是用旧主体的问法去问新主体的处境。因果链：形成——主体性错位；解决——本体性改变，即主体性革命；结果——主体性重生。
- 承重命题照附录一原话；三条守线：复合主体不先在；重生不是复活；不以「一个人」作发动者。
- 四十户人家都是构想；无调查数据、无用户试验；不作诊断；真实代价不说成会消失。
