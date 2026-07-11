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
- 手动清除：控制台 `clearReflect('claude:pro')` 清单个、`clearReflect()` 清全部，强制重写。

## 铁律四 · 境外基底走流式（不撞代理超时）

- 境外基底（GPT/Claude/Gemini）经 `/api/llm-proxy`（源码在 `src/worker.js`，代理已流式透传 `upstream.body`，勿改成 buffer）。
- 前端必须流式：`buildPayload` 给 Claude/GPT 加 `stream:true`，Gemini 用 `:streamGenerateContent?alt=sse`；`callOverseas` 用 reader 逐块读 SSE，按三家格式解析 delta（OpenAI `choices[].delta.content` / Anthropic `content_block_delta→delta.text` / Gemini `candidates[].content.parts[].text`）。
- 为什么：非流式时服务端要等全部生成完才返回，撞 Cloudflare ~100s 网关墙，Claude 的长心得和 16000-token 论文步骤必挂。流式首字节几秒到达，永不超时。
- **别改回非流式**。心得也因此可以放心写满 5000 字（`REFLECT_MAX_TOKENS = 8000`）。

## 其它约定

- **前台零 SDE 术语**：发生器面向公众，武器锻造第五律——前台不出现"SDE/发生学/纠缠"等黑话（内功在后台跑）。
- Key 分存：`sde_ds_key / sde_glm_key / sde_claude_key ...`，全程只在浏览器 localStorage，国产直连、境外经代理只转发不存储。
- 快速档模型名要用真实存在的（如 `claude-sonnet-4-6`，别用不存在的 `claude-sonnet-5` 会 404）。
- 改 JS 后先 `node --check`；改 HTML 检查标签配对；改完照 `sde-website-ops` 流程 push + 验证构建 success。
