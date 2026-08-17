# 专著第 92 号《谁来陪伴我？》工程链

AI 时代的婚姻困境 · 王德生 ＋ Claude 编著 · ISBN 979-8-90690-040-1 · 135 页 · 7.6 万汉字

## 源文
- `ch/c01–c10.md` 十章改写稿（源自站内十位作者的十篇论文，**全部重写**）
- `ch/sn.md` 枢纽章 · `ch/hz.md` 合章
- `front/front.md` 出版信息·作者介绍·前言·导读·导论·四编编序
- `back/back.md` 结语·三附录·全书十句·后记·封底
- `front_refs.md` 参考书目（由十篇原篇文献表合并，245 条）

## 构建
1. `thicken.py` 加厚补丁（幂等，已执行）
2. `asm.py` → `manuscript.md`。层级：`# ` 编扉页 / `## ` 章级部件 / `### ` 节 / `#### ` 小节。前后件在装配时整体降一级（`demote`），避免与章级 `##` 撞车
3. `build_docx.py` → docx；`soffice --headless --convert-to pdf`
4. `mkpagemap.py` → `pagemap.json`；再 `build_docx.py withpage` 重出，**两遍构建**取目录页码，第三次跑 mkpagemap 复核漂移应为 0
5. `cover.py` → cover.jpg / cover-full.jpg
6. `publish92.py` → `public/books/m/92/text/`（29 页）+ read.html；`landing92.py` 落地页；`insert92.py` /books/ 插卡

## 踩过的坑
- **改号**：第 90/91 号被并发会话占走（付自文《文心探幽》卷一卷三），本书由 90 改为 92，ISBN 由 029-6 改为 040-1。改号须同步七处：front.md 出版信息、build_docx 扉页、cover.py（封面／封底／条码数字串）、publish/landing/insert 三脚本
- **`str_replace` 插节时必须把锚点标题接回 new_str**，否则会误删该标题（本轮曾误删三个节标题：c02 五/六节、c03 五节，已复原）
- `mkpagemap.py` 的标题匹配须两条并用：页首 + 按稿本次序单调向后；附录三因节标题紧随其后，加了「前三字开头 + 其余出现在页首 70 字内」的兜底
- 版式：170×240mm，正文 9.5pt / 行距 1.35，边距 17/15/16/15mm
