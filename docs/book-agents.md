# 每本专著自己的智能体（2026-10-03 起）

王德生令：不是一个通用的「书生」，而是**每本书一个独特名字的智能体**，带着**为这本书提前打造的碰撞库**（RAG），能检索到站上其他专著与文章来碰撞这本书——出版的价值由此典范转移。

## 构成

| 件 | 位置 | 说明 |
|---|---|---|
| 名字与人格 | `public/books/agents.json` | 每本书：`name`（2–3 字，取自书本身的核心意象，**全站唯一**）、`epithet` 称号、`intro` 自我介绍、四道门的开门问题 `starts` |
| 核心要点（常驻记忆） | `public/books/m/N/keypoints.json` | 每本至少 10 条（现为 12 条左右）、每条约 200 字：依据全书各章摘读提炼，用书本身的术语，标出处章名。每一问都整份带上，长书读不全时以它为全书骨架。由 AI 依摘读件提炼（`tools/make_book_digest.py N` 出摘读件，`tools/check_keypoints.py N` 校验条数与字数） |
| 专属碰撞库 | `public/books/m/N/rag.json` | `tools/build_book_rag.py` 离线生成：全站专著（按章）＋文章切段，字符二元 TF-IDF，按本书每一章检索；专著与文章各 12 条，专著里至少 5 本跨书类；标「同源／同向／跨界」、撞本书哪一章、共有字串 |
| 智能体页 | `public/books/m/N/agent/` | `tools/build_book_agents.py` 生成的壳，共用 `public/books/agent/app.js`＋`app.css` |
| 名录 | `public/books/agent/` | 全部智能体；旧链接 `?m=N` 自动跳到各书自己的页 |
| 入口 | 书架卡片「「名字」· 和这本书对话」＋ 详情页入口块 | `build_bookshelf.py` 生成卡片，并自动调用 `build_book_agents.py` 与 `inject_book_agent.py` |
| 服务端 | `src/worker.js` | `/api/wds/read` 与 `/api/wds/read-paper` 的 `bookagent` 档：`WDS_SHUSHENG_SYS`（名字、五道门、四条铁规、专属碰撞库）；有 `bookRag` 时不再现场检索 |

每一问，页面按问题与当前这道门从碰撞库里挑最相撞的 10 条递上去（对撞、拆开两道门优先「跨界」、压低「同源」），答案下方列出这一问用了哪几条。

## 新书上站时

1. 在 `agents.json` 里给它起名（先查重名）；
2. 出核心要点：`DIGEST_DIR=/tmp/d python3 tools/make_book_digest.py N` → 依摘读件写 `public/books/m/N/keypoints.json`（格式照任一本已有的）→ `python3 tools/check_keypoints.py N`；
3. `python3 tools/build_book_rag.py N`（约 2 分钟语料＋每本约半分钟；全量重建约一小时，建议每周一次）；
4. 照常跑 `python3 tools/build_bookshelf.py`——智能体页、详情页入口、书架卡片一并更新。

没起名的书暂用「书生」兜底，`build_book_agents.py` 会点名提醒；没有碰撞库的书退回现场检索全站。

## 验证

`node tools/sim_shusheng.js`（服务端提示语与分支）。
