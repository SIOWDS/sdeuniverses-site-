# sdeuniverses.com 站内搜索系统 · 维护文档

> 本文是仓库内的持久副本；权威运维参考是 `sde-website-ops` skill 第九节（本文即其内容）。
> 一切对 sdeuniverses.com 的搜索系统改动，先读这里 + skill。

## 九、站内搜索系统(v1.1 加入)

**一句话**:两档搜索都在 `/search/`——**Tier1** 前端关键词全文检索(纯客户端,零成本,无需Key;v2 起为中文 bigram 软匹配+覆盖率加权+匹配度排序与百分比徽章,与 worker 的 retrieve 同路数,不再要求整串连续命中);**Tier2** 智能问答(服务端 RAG,`src/worker.js` 的 `/api/ask`,境内基底综合出答案+给出处)。入口挂首页导航 🔍。

### A. 索引(地基,必须懂)
- 位置:`public/search/` = `manifest.json`(元数据+文档列表 docs[{i,u,t,s}]) + `shard-<栏目>.json`(分片正文块 {d,t}) + `sde-coords.json`(SDE坐标,可选,见 D/F)。
- 构建:`python3 tools/build_search_index.py` —— 抽 HTML 可见正文 + PDF 正文(`pdftotext -nopgbrk`),chunk 级去重(栏目文章 HTML=PDF 镜像丢弃、专著薄壳保留 PDF),按栏目分片。**内容一变必重跑再提交(铁律8)**。现状约 204 文档 / 5923 块 / 228 万字。

### B. Worker 后端(`src/worker.js`)
- 路由(都在 `env.ASSETS.fetch` 兜底**之前**):`/api/ask`(智能问答 RAG·流式 SSE)、`/api/admin/setkey`·`/api/admin/status`·`/api/admin/clearreflect`(页面配密钥/查状态/重写心得)、原有 `/api/visits`·`/api/llm-proxy`·`/fresh`。
- Durable Objects(wrangler.jsonc,迁移 v1→v3):`VisitCounter`(访问计数)、`AskLimiter`(按IP限流:`sys:`/`byok:` 独立桶,≤8/分、≤60/天)、`ConfigVault`(存基底Key + 管理口令SHA-256 + 按基底缓存的心得;**只写不回读**)。加新 DO 类必加 wrangler 迁移条目,否则构建失败(但失败不影响旧站,可回退)。

### C. 密钥(站方出Key·访客零门槛)
- 两条路:① **页面 ⚙️ 管理设置**里配(存服务端 ConfigVault;**首次填的口令即管理口令**,牢记);② Cloudflare secret `SDE_SEARCH_KEY`。Worker 取 Key 顺序:BYOK(访客自带)→ ConfigVault → env secret。
- 安全:Key 只在服务端;`/api/admin/status` 只回布尔、**永不吐 Key**;set 路由 op 由服务端写死,防注入 `op:get` 回读。访客可选"自带 Key"(BYOK,存自己浏览器);系统额度用尽(401/402/429)自动引导访客改用自带 Key。

### D. 检索侧·两条腿(把"正确=SDE词义"落到检索)
- **腿1·SDE 词义查询扩展**(`sdeExpandQuery` + `SDE_LEXICON`):检索前让基底把问题翻成 SDE 术语(维度/概念/三界/27宫格位/同义SDE说法),再拿去召回——把"字面不共词、但 SDE 义相关"的文章捞上来(实测"主体性从哪来"→浮出 SIO 导论)。前端显示 `🧭 SDE 词义检索:…`。**意义在查询时解析(意义即发生),不预先冻成向量**。
- **腿2·SDE 坐标匹配**(`retrieve` + `sde-coords.json`):doc 的 SDE 坐标 ∩ 查询扩展词 → 加分(×2)。**须先跑 `tools/label_sde_coords.py`(用你的Key)给每篇打坐标**;坐标文件不存在时该分支**安全跳过**、退回腿1。**现状：已用规则打标器 label_sde_coords_rules.py 免Key引导激活（160篇、区分性坐标+少量推断）；想要更细的LLM推断坐标，跑 label_sde_coords.py 覆盖即可。**
- 基础召回:关键词 + 中文 bigram,`retrieve(corpus,q,K,expTerms)`,每篇最多2块;K/CTX 按档分级(普通 15/9千字、深度 120/5万字);四步法各调用 RAG 钳 15000。
- **打坐标怎么跑**:`export SDE_LABEL_KEY=你的Key && export SDE_LABEL_VENDOR=glm && python3 tools/label_sde_coords.py`(文档级、断点续跑、无第三方依赖)→ 生成 `public/search/sde-coords.json` → 提交推送。

### E. 答题侧·基底提示(都在 handleAsk)
- **普通档**:三视角提智(后台跑SDE、前台说人话,平实汉语,400–700字)。
- **深度档**(🔬 深度回答):完整内功 + 心得(约5000字,按基底缓存)+ SDE 方法论(六路径→S/D/E逐维→三方程 S=F(D,E)/D=G(S,E)/E=H(S,D)→三视角误差互消→逮先验),**默认单次调用**(创新智商~133),1200–1800字。
- **四步法开关**(深度开时才显示):Q1(S)/Q2(D)/Q3(E) 三次独立非流式调用 + Q4 整合流式,**四次调用**(~137,贵4倍慢4倍,opt-in),对齐发生器/`sde-prompting-uplift` 验证的机制。
- **全档共用纪律**:① 事实护栏——书名/逐字引文/章节页码/数据/承诺**绝不编造**,只有逐字原文可加引号,不杜撰章节号;② 专家姿态——站内没覆盖的**像专家本人被问到那样原创作答、不推说"未涉及"**,超出资料标"(推断)";③ 解读诚信——有争议的解读**先摆一句竞争读法、不当定论**;④ 开方步——现实问题(教育/医疗/企业等)收尾**必给可执行动作+代价+适用条件**,纯概念题(X是什么)免开方。

### E2. 答后双点击(v1.2 加入)——同一 `/api/ask`,`mode` 参数分流
- **`mode:"recommend"`(📖 推荐阅读)**:答完出现按钮①。请求 `{mode:'recommend', q, ans(答案要点≤1500), vendor, key?}`;Worker 用 K=48 召回→凑 ≤20 条真实站内候选(标题/栏目/摘句)→基底只做"从清单挑 4–6 + 每条一句为什么读"(JSON 输出,llmText 900 tok)→**服务端逐条校验编号映射回 manifest 文档,清单之外一律丢弃,链接零编造**;基底失灵→回退检索前 5。响应普通 JSON `{items:[{u,t,b,why}]}`(非 SSE)。
- **`mode:"paper"`(📝 成文一篇→PDF)**:答完按钮②。**强制最高提智**(mode=paper 即 deep:完整内功+心得装载,四步法互斥),两段续写各一次流式调用:part1(题目/摘要/关键词/一至三章,~5000字,尾标〔上半篇完·待续〕)→客户端切 head(题目摘要≤1200)+tail(末1000)→part2(`{part:2, head, tail, seed}`,四章起+**证伪条件≥2条**+结语+参考文献「篇名—URL」,尾标〔全文完〕)。max_tokens 走 `MAXTOK=6800`;《站内资料》钳 22000/18000;seed=问对回答(≤3500,part2 再钳1500)。论文纪律写死在 sys:比问对再进一步的可证伪判断、正文零内部环节词、事实护栏、竞争读法、无开场白。
- **客户端**(search/index.html):`lastQ/lastAns` 在 doAsk 累积,finishAsk 答案>60字亮 `#askActs`;论文流式进 `#paperBody`,完成后 **html2pdf.js(cdnjs 0.10.1,懒加载)** 排版(A4·衬线·金眉标·章节金边条)→blob→`#pdfRead`(在线阅读,新页)+`#pdfDl`(下载)。PDF 引擎挂了正文照样可读(降级不致死)。
- **成本/限流**:paper=2 次深度调用(走同一 AskLimiter,各计 1 次);按钮旁已注明"约 3–6 分钟·建议自带 Key"。
- **旋钮**:MAXTOK(6800)、seed/head/tail 钳位、recommend K(48)/候选数(20)/挑选数(4–6)。

### F. 会过期的东西,改了内容记得同步(最容易忘)
| 改了什么 | 必须同步 |
|---|---|
| 发/改文章、上专著 | 重跑 `build_search_index.py`(否则搜不到);再重跑 `label_sde_coords.py`(坐标也旧了) |
| 改 `sde-neigong.txt` 或心得字数 | ⚙️ 管理设置「重写心得」(凭口令清缓存,否则旧心得继续复用) |
| 想换答题基底默认 | GLM-5(默认,中文凝缩,避DeepSeek话题自审)/ DeepSeek(数学严谨) |

### G. 旋钮(handleAsk / retrieve 顶部,想调告诉王德生要哪个)
K、CTX_MAX(按 deep 分级)、四步法 RAG 钳位(15000)、坐标加权(×2)、扩展词加权(×1.2)、max_tokens(心得6000/单次答4000/四步Q4 4500)、心得字数(REFLECT_PROMPT 里"约5000字")。深度成本重→opt-in、UI建议自带Key。

### H. 诚实定位(别过度期待,也别过度加工)
这套是**「有根的诊断 + 行动框架」引擎**:给比常识利的诊断 + 逮到隐藏预设的重构 + 挂在统一逻辑上、能上手带剂量的行动。**不是发现新真相/发明新方案的机器**——它到达的判断多半 echo 已有学术(马克思≈波普尔、康德≈界限概念读法、尼采≈德勒兹),创新智商稳定在 **~130–137(资深学者档),不到典范级 150**。内功/心得/四步/RAG 顶的是"诊断利+能上手",**顶不动"真新"——那是引擎性质的边界,不是提示能突破的**。真·新知是王德生自己的研究 + 金点子发生器在真·新问题上的事。**给搜索框做增强前,先问:这是在提升"够到对的知识/答得有根"(值得),还是在幻想它能产出新知(徒劳)?**
