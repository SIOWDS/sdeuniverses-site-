# tools/

## build_roster.py — 重建学员名单

学员名单页 `/students/` 由 `public/students/roster.json` 驱动（前端 JS 按"发表活跃度分数"自动排序）。

**这个文件不要手改。** 跑：

```bash
python3 tools/build_roster.py            # 重建并写回
python3 tools/build_roster.py --check    # 只比对不写，有差异退出码 1（提交前自检）
```

### 为什么

`roster.json` 里的 `papers` / `count` 是**派生数据**——谁发了哪篇、哪天发的、多少字，这些事实已经写在已发布的页面里了。手工维护一个派生文件，必然出两类事故，而且都出过：

- **漏更**：发表提交忘了带上 roster。7-16 整批（葡萄、张琼、陈晓艳）这么丢过一次，秦莉 7-17 的两篇又丢过一次——页面已经上线，名单里却显示 0 篇。
- **撞车**：两个 agent 同时改这一个文件 → rebase 冲突。手工解冲突时方向极易搞反（rebase 期间 `--ours` 是上游、`--theirs` 是你正在重放的提交，与直觉相反），一不小心就把对方的数据整段抹掉。

改成从磁盘派生后，两类事故一起消失：页面在磁盘上，扫描就看得见，不依赖谁记得更新。

### 冲突了怎么办

**不要手工挑拣冲突块。** 论文页各在各的路径、天然不冲突，所以合并后磁盘上已经是双方成果的**并集**：

```bash
git checkout --ours public/students/roster.json   # 任选一边收下，哪边都行
python3 tools/build_roster.py                     # 从并集重新派生 → 正确答案
git add public/students/roster.json
git rebase --continue
```

### 它怎么认作品

- **一件作品** = 含 `index.html` 的**叶子目录**（其下再无 `index.html` 子目录）。
- 排除约定的索引页目录名：`works`、`submit`。
- 合集容器（如 `qin-li/essays/`、`qin-li/poems/` 下各有多篇）会自动下潜一层。

不靠模板特征识别（如 `class="art-title"`）：各学员页面模板并不统一——秦莉的诗与评论就是另一套，压根没有 `art-title`。结构判据才靠得住。

- **发表日期**：优先取页面自报的 `发表于 YYYY年M月D日`（发表规格的强制字段），缺失则用该文件首次进入 git 的日期兜底。
- **字数**：用 HTML 解析器跳过骨架（nav/footer/readbar/topbar/endbox 等）后数字符。**不要用正则剥离骨架**——`<div class="topbar">.*?</div></div>` 这种写法靠猜嵌套，`.*?` 会停在文档里第一个 `</div></div>`，把正文整段吞掉（《黑咖啡》那首诗就这么从 319 字缩成过 31 字）。

### 仍然手工的字段

`slug` / `name` / `small` / `enrolled_order` 是学员身份信息，磁盘上推不出来，继续由 `roster.json` 承载——只有新学员报名时才动。生成器只覆盖 `papers` 与 `count`。
