# 金点子发生器 · 维护须知（心得机制 / 基底 / 流式）

文件：`public/taste/idea-generator/index.html`（单文件，约 2600 行）

供任何接手者（Claude Code / Cowork / 人工）在改这个文件前必读。以下是几条**已用鲜血换来的铁律**，改动前逐条对照，任何一条都不许破坏。

---

## 铁律一 · 基底与心得一一对应（最重要）

- 每个基底（DeepSeek / GLM / Kimi / 千问 / GPT / Claude / Gemini，pro/flash 各算一个）**有且只有它自己亲手写的那一份《从发现到发生》心得**。
- **绝不可**跨基底串用；**绝不可**"固定用某个稳定基底（如 DeepSeek）代写心得再给别的基底用"。
- 为什么：心得是"该基底**亲手**把发生学内化"的产物，是两次内功提智的灵魂。换写手 = 丢灵魂，提智就废了。这一点用户明确定过性，且反驳过"固定 DeepSeek 代写"的方案。
- 代码保证：缓存键 = **纯基底**（`reflectionRoundKey(writeSel)` 只返回 writeSel）；存 / 取 / 写全部按 `writeSel` 隔离。localStorage 键 = `sde_reflect_<VER>_<基底>`。
- **禁止的改法**：任何"共用一份心得""固定某基底代写""合并/平均多基底心得"的改动，都违反本铁律。

## 铁律二 · 心得与"具体问题"无关，按基底缓存

- 心得 prompt（`reflectPrompt` = `SDE_BASE + REFLECT_SPEC`）里**不含用户的问题**——它是对发生学的通用内化自省。
- 所以缓存键**只按基底、不带问题**：换问题不重写，换基底才重写。
- 别退回"基底+问题"的键（那会每换一个问题就重写一次，纯浪费）。

## 铁律三 · 心得本地持久化（写一次，永久复用）

- 三级缓存（`getSharedReflection`）：① 内存（同会话）→ ② localStorage（跨刷新/跨会话/隔天）→ ③ 真正写一次，写完存盘。
- **长度守卫**：只缓存 >1500 字的心得，绝不缓存写失败/被截断的残缺心得。
- **版本号** `REFLECT_LS_VER`：内功文件（`sde-neigong.txt`）或心得规范（`REFLECT_SPEC`）**一旦升级，必须把它 +1**，否则用户会用到旧内功写的过时心得。这是改内功时最容易忘的一步。
- **版本号的第三种触发（2026-07-12 教训）**：某档位的**底层模型一旦更换**（如 qwen:pro 从 qwen-max 换 qwen-plus），同样必须 bump 版本并迁移——缓存键是档位名（writeSel），换模型后旧心得就不是"这个基底"写的了，直接继承违反铁律一。迁移写法见 index.html 内 v1→v2 迁移块：其它基底搬运保留，仅换模型的档位作废重写。
- 手动清除：控制台 `clearReflect('claude:pro')` 清单个、`clearReflect()` 清全部，强制重写。

## 铁律四 · 境外基底走流式（不撞代理超时）

- 境外基底（GPT/Claude/Gemini）经 `/api/llm-proxy`（源码在 `src/worker.js`，代理已流式透传 `upstream.body`，勿改成 buffer）。
- 前端必须流式：`buildPayload` 给 Claude/GPT 加 `stream:true`，Gemini 用 `:streamGenerateContent?alt=sse`；`callOverseas` 用 reader 逐块读 SSE，按三家格式解析 delta（OpenAI `choices[].delta.content` / Anthropic `content_block_delta→delta.text` / Gemini `candidates[].content.parts[].text`）。
- 为什么：非流式时服务端要等全部生成完才返回，撞 Cloudflare ~100s 网关墙，Claude 的长心得和 16000-token 论文步骤必挂。流式首字节几秒到达，永不超时。
- **别改回非流式**。心得也因此可以放心写满 5000 字（`REFLECT_MAX_TOKENS = 8000`）。

## 铁律五 · 涌现工序执行五重检验（v1.1，2026-07-12 升级）

- 涌现规格（`EMERGE_SPEC`）已按 `sde-goldpoints-to-paradigm` Skill 规程完整显式化，并打上 v1.1 两刀：
  - **四重检验 → 五重检验**：新增 ⑤ 证伪条款——新典范必须自带 ≥2 条可操作证伪条款（其中至少一条正面接住"最扎手的反例类"），缺则作废重做。
  - **"不可消解" → "近邻切割"**：必须点名 ≥3 个最近邻概念/理论，逐个给出确切差别或承认重叠；"不能被替代"一句话不算通过。
- 为什么：实测三次（GLM 涌现 F=118、Claude 发生器版 F=122、手工版对照）证明**证伪纪律在金点子阶段有、在涌现阶段断档**，新典范全被 F 维拖死在 140–142。此升级即管线断档修复。
- 输出结构相应变为六节：碰撞→暗流→新典范（五重检验）→**证伪条款**→跨学科地图→**旗帜的来历**（防遗忘条款：新典范是有来历的旗，不是被发现的本质）。
- 下游 PAPER_SPEC 转述已同步"五重检验"；无 JS 解析依赖，输出结构可安全演化。
- **语言纪律**：EMERGE_SPEC 内已清洗"真判断/真差异/真深度"等"真X"强调格与"本体论级"修饰词——将来改这段 prompt 时同样禁用。
- 本次改动不涉及 REFLECT_SPEC/内功文件，**无需 bump REFLECT_LS_VER**。

## 其它约定

- **前台零 SDE 术语**：发生器面向公众，武器锻造第五律——前台不出现"SDE/发生学/纠缠"等黑话（内功在后台跑）。
- Key 分存：`sde_ds_key / sde_glm_key / sde_claude_key ...`，全程只在浏览器 localStorage，国产直连、境外经代理只转发不存储。
- **思想拓展功能声明（强制项，2026-07-12）**：本智能体产出的定位声明。单一来源常量 `THOUGHT_DECL`（页面 `thoughtDeclBar` 常驻 + 六个导出通道全部内嵌：四篇/第二批 HTML-Word、涌现/单篇/六篇 docx、学术 PDF）。**将来任何新增导出通道必须带上此声明**（HTML 用 `THOUGHT_DECL_HTML`，docx 用 `thoughtDeclPara()`，模板字面量直接 `${THOUGHT_DECL}`），不许遗漏。改文案只改 THOUGHT_DECL 一处。
- 顺手修复（同日）：第二批 Word 导出的双重转义 bug——分段正则曾写成 `/\\n{2,}/`（匹配字面反斜杠n，永不命中→整篇塞进一个巨型段落）+ BOM 写成字面 `\ufeff` 文本；已改回 `/\n{2,}/` 与真 BOM。
- 快速档模型名要用真实存在的（如 `claude-sonnet-4-6`，别用不存在的 `claude-sonnet-5` 会 404）。
- 改 JS 后先 `node --check`；改 HTML 检查标签配对；改完照 `sde-website-ops` 流程 push + 验证构建 success。
