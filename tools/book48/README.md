# 第 48 号《三律心理学》精选本（约 20 万字）

从 `public/books/m/48/quanben/text/`（七十万字全本网页版）按选篇清单编出精选本。

## 编稿
1. `units.py` —— 把全本各篇切成子篇单元，写 `units.json`。
2. `compile.py` —— 按 `PARTS` 选篇清单抽取原文，接回 PDF 断行，还原误标为列表的正文段落，
   去掉篇内旧章号，修订编序/编结对未选篇目的提法，再交 `polish.py` 打磨，写 `book.json`。
3. `polish.py` —— 排版级修复（文字论断不改）：
   - 表格复原：原稿把表格压成乱序文字；`tables.py` 从全本原版 PDF 提取 205 个表格（`orig_tables.json.gz`），
     `tmatch.py` 按内容匹配后换回真表格（39 张），合并跨页续表；
   - 表情符号与缺字符号清理，「📌 金句收束：」类标签改加粗；
   - 章内伪标题规范化（章内「第X编」改称「第X部分」）、编号句、短行小标题、断句接回；
   - 删去选篇后悬空的标题、写作残留语、指向未选内容的「下一章」预告。
4. `to_md.py` —— 生成排版稿 `manuscript.md`。

## 排版
`build_book_local.py` 是 sde-popular-philosophy-style `build_book.py` 的本地副本，改动：
目录点线改表格布局（WeasyPrint 70）、编首页只放编名、编序另起一页、章内分部标题样式、表格样式、
要点句强调框、`TIGHT` 环境变量按章微收紧行距以消除章末孤页。

    TIGHT='{"f总序":2,"c1":1,"c6":1,"c12":1,"c14":1,"c20":1,"c21":1,"c22":1,"c24":1,"c29":1}' ./rebuild.sh print
    TIGHT='{"c3":1,"c8":1,"c11":1,"c16":2,"f全书总结":1}' python3 build_book_local.py manuscript.md --out sanlv48 --edition reader ...

`pagestats.py` 检查每页行数（找孤页），`sheets.py` 生成全书缩略图供逐页审阅。

## 网页
`gen_web.py` —— 生成 `public/books/m/48/text/`（需先从 PDF 书签导出 `outline.json`）。

脚本里的路径指向编稿时的临时目录，重跑前按需调整。
