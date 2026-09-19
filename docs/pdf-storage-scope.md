# PDF 存储的适用范围（2026-09-19 核定）

写这份是因为铁律七的措辞会引出一次误清仓。

## 事实

| 前缀 | Worker 是否从 R2 取 | 现状 | 能否迁桶 |
|---|---|---|---|
| `/students/**.pdf` | **是**（src/worker.js 有 `/^\/students\/[^?]+\.pdf$/i` 拦截，落空回落 ASSETS） | **git 里 0 个**，18 个已于本日写入桶并逐个核过 | 已迁完 |
| `/books/m/**/*.pdf` | **否**——Worker 没有这个前缀的拦截 | git 里 96 个 | **现在不能**。r2-put 只放行 `students/**.pdf` 与索引键 |
| `/art/**/*.pdf` | 否 | git 里若干 | 同上 |

## 由此两条

1. **专著 PDF 留在 git 不是违纪。**它们没有桶通道：即便写进桶，Worker 也不会去桶里取。
   把它们从 git 删掉，当场 404。
2. **铁律七说的「PDF 一律不进仓库」，实际范围是 `public/students/`。**
   2026-09-19 之前那句话的事实基础已经不成立过一次——git 里悄悄长回了 18 个学员 PDF，
   而它们一个都不在桶里，全靠 ASSETS 兜底。这正是那条纪律描述的潜伏回归，只是没人去核。
   现已写桶、逐个 r2-check、按原 URL 真取回比对字节、再从 git 删除，并在 .gitignore 加了
   `public/students/**/*.pdf`。

## 要把专著 PDF 也迁桶，须先做三件事（属开发任务，不是发布任务）

1. `src/worker.js` 增加 `/books/**/*.pdf` 的 R2 拦截（保留 Range 支持，PDF.js 分块取要它）；
2. `/api/admin/r2-put` 的路径白名单放行 `books/` 前缀；
3. 跑 `node tools/sim_r2_pdf.js`，并做一次真 round-trip（写→check→按原 URL 取回比对字节）——
   源码检视式的 sim 抓不到这类错，得靠线上黑盒。

**在这三件做完并验证之前，任何"清理 /books 下 PDF"的动作都会让 96 本书的 PDF 当场 404。**
