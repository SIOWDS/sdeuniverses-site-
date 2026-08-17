# 专著第 92 号《谁来陪伴我？》工程链

AI 时代的婚姻困境 · 王德生 ＋ Claude 编著 · **ISBN 979-8-90690-034-0** · 224 页 · 约 14.6 万汉字

## 版本谱系
- 第一版：135 页 / 7.6 万字（十章改写，ISBN 曾拟 029-6 → 因 90/91 被并发会话占用改为 92 号 / 040-1）
- 第二版：141 页 / 8.1 万字（件次体检：补封面图页、前言扩到 4,109 字、目录移到导读之后）
- **第三版（现行）：224 页 / 14.6 万字** —— 从十篇原材料搬运营养（`haul1–14.py`），并按用户指定把 ISBN 改为 **034-0**（校验位已回验；站上 034 此前未占用）

## 源文
`ch/c01–c10.md` 十章 · `ch/sn.md` 枢纽章 · `ch/hz.md` 合章 · `front/front.md` · `back/back.md` · `front_refs.md`（245 条）

## 构建
1. `haul1–14.py` 搬运补丁（幂等，已全部执行；`thicken.py` 是第二版的加厚补丁）
2. `asm.py` → `manuscript.md`。层级：`# ` 编扉页 / `## ` 章级部件 / `### ` 节 / `#### ` 小节；前后件装配时整体降一级
3. `build_docx.py` → docx；`soffice --headless --convert-to pdf`
4. `mkpagemap.py` → `pagemap.json`；再 `build_docx.py withpage` 重出，**两遍构建**取目录页码，第三次跑 mkpagemap 复核漂移应为 0
5. `cover.py` → cover.jpg / cover-full.jpg（封底条码数字串 `9 798906 900340`）
6. `publish92.py`（text/ 30 页）· `landing92.py`（落地页）· `insert92.py`（/books/ 插卡）

## 踩过的坑（三条都吃过亏）
1. **往稿件里插节，new_str 必须把锚点标题接回去**，否则会误删该标题。本工程先后误删过四个标题（c02 五/六节、c03 五节、附录三第四节），全部事后复原。⇒ 一律走落盘的 patch 脚本（带 `assert anchor in s` ＋ `text[:24] in s` 幂等判断），禁止裸 str_replace
2. **新增附录须同时改三处**：`asm.py` 的装配行、`publish92.py` 的 `{'一':'ap1',...}` 映射表（漏了会 KeyError）、落地页/卡片的"N 附录"文案
3. **改号／改 ISBN 须同步七处**：front.md 出版信息、build_docx 扉页、cover.py（封面／封底／条码数字串）、publish/landing/insert 三脚本；改完必须重跑 asm→docx→PDF 两遍构建

版式：170×240mm，正文 9.5pt / 行距 1.35，边距 17/15/16/15mm。终检：豆腐块 0，目录 29/29 全命中，两遍构建漂移 0。
