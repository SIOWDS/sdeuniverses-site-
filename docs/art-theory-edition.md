# SDE艺术论 · 2026年9月增订版

本版依用户要求在第220号《我的三个宝贝》的成书风格上，为全部32章增加案例与大白话解释。

- 新增正文 **50,179 个汉字**，不含96个新增小节标题；计入小节标题共 51,579 个汉字。逐章统计保存在 `content/art-theory/expansion-counts.json`。
- 采用 Unicode U+4E00–U+9FFF 统计汉字，不把标点、字母、数字和空白计入5万字目标。统计只覆盖32章的新增段落，前言说明另计。
- 保留原有三部32章、两份附录、47项参考资料、32个章首引句与32个章末提炼。各章新增3节，原收束节顺延；第20章顺延至第7节，其余顺延至第8节。
- 新增日常人物、对话、课堂、工作与家庭场景均为构造案例，前言统一说明；历史作品与思想文本依据原作及书后资料。自拟诗与假设改写明确标示。
- 暖纸色、深蓝标题、金色章码、引句和章末菱形沿用上一版。190×250毫米，当前PDF **226页**。
- 单一正文源：`content/art-theory/revised-2026-09.json`。PDF、全文网页、封面和封底由 `tools/build_art_theory.py` 生成。
- 重建：`python3 tools/build_art_theory.py --source content/art-theory/revised-2026-09.json --out /tmp/art-book --fonts /path/to/fonts`。字体需有NotoSerifSC-Regular.ttf、NotoSerifSC-Semibold.ttf；依赖reportlab、pypdf、PyMuPDF。
- `content/art-theory/page-map.json` 是翻页目录依据；印刷页1对应PDF物理页2，offset=2。重新排版后必须用新page-map重建read.html。
- PDF与封面缓存版本 `20260930-expanded50k`；阅读进度键同版更新，避免旧页码误定位。
- 网站继续使用本仓库main分支的Cloudflare发布流程。只更新art-theory目录条目，再通过tools/build_bookshelf.py生成书架；保留其他书籍的并发更新。
- 未分配新的专著编号、ISBN或售价。
- 书架保留 `publishedAt` 的首次上线日期，以 `editionPublishedAt=2026-09-30T12:28:12Z` 记录增订版实际上线时间；`tools/build_bookshelf.py` 取两者中较晚的一次排序，确保新版出现在默认书架前列。三个书架入口均由同一目录生成。
