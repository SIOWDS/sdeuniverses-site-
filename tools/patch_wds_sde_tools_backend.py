#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""问WDS v3 · 第二批（后端）
给 /api/wds/chat 加 `tool` 字段：九道 SDE 工序（评分/三视角/母题/近邻/改姓/缝隙/碰撞/九宫/坐标），
每道注入一段「本轮工序」硬要求到 system。近邻那道要真名单，故把 /api/kb/neighbors 的
取名单+合并逻辑抽成共用 nbrFor()，端点与工序共用一份（判据/召回复制两份就会静默漂）。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "src", "worker.js")
with io.open(W, encoding="utf-8") as f:
    s = f.read()


def sub1(s, old, new, what):
    assert old in s, "锚点没找到：" + what
    assert s.count(old) == 1, "锚点不唯一（%d 处）：%s" % (s.count(old), what)
    return s.replace(old, new, 1)


# ════════════════════════════════════════════════════════════════════
# 一、把近邻取名单抽成共用 helper（端点与「近邻工序」共用一份）
# ════════════════════════════════════════════════════════════════════
OLD_EP = '''      try {
        const pubs = await loadPubs(env, url);
        let list = nbRank(pubs, q, k + 6, { author: author });
        const seen = Object.create(null);
        for (const x of list) seen[x.u] = 1;
        if (wantSite) {
          // 只多取一小把，够补上 publications 覆盖不到的栏目即可，不为它加检索预算。
          try {
            const lr = await lightRetrieve(env, url, q, [], 8, 900, { pick: 8 });
            for (const ck of (lr.hits || [])) {
              const d = lr.corpus.docs[ck.d];
              if (!d || !d.u || seen[d.u]) continue;
              if (/^\\/students\\//.test(d.u)) continue;   // 学员篇目已由 publications 一路覆盖且带判断句
              seen[d.u] = 1;
              const first = String(ck.t || "").replace(/\\s+/g, " ").trim().slice(0, 120);
              list.push({ t: d.t, u: d.u, kind: "", line: first, au: "", own: false, score: 1 });
            }
          } catch (e) {}
        }
        list = list.sort((a, c) => c.score - a.score).slice(0, k);
        return Response.json({ neighbors: list, block: nbBlock(list), n: list.length, terms: nbTerms(q).length }, { headers: _cors() });
      } catch (e) {'''
NEW_EP = '''      try {
        const list = await nbrFor(env, url, q, k, author, wantSite);
        return Response.json({ neighbors: list, block: nbBlock(list), n: list.length, terms: nbTerms(q).length }, { headers: _cors() });
      } catch (e) {'''
s = sub1(s, OLD_EP, NEW_EP, "近邻端点改走 helper")

HELPER = '''// 取一份站内近邻名单。**端点 /api/kb/neighbors 与「近邻工序」共用这一份**——
// 召回逻辑一被复制两份就会漂，而这种漂是静默的：一边改了口径，另一边照跑，
// 只是从此少召回几篇、概念被第二次发明，没有人收到报错。
async function nbrFor(env, url, q, k, author, wantSite) {
  const pubs = await loadPubs(env, url);
  let list = nbRank(pubs, q, k + 6, { author: author || "" });
  const seen = Object.create(null);
  for (const x of list) seen[x.u] = 1;
  if (wantSite !== false) {
    // 只多取一小把，够补上 publications 覆盖不到的栏目即可，不为它加检索预算。
    try {
      const lr = await lightRetrieve(env, url, q, [], 8, 900, { pick: 8 });
      for (const ck of (lr.hits || [])) {
        const d = lr.corpus.docs[ck.d];
        if (!d || !d.u || seen[d.u]) continue;
        if (/^\\/students\\//.test(d.u)) continue;   // 学员篇目已由 publications 一路覆盖且带判断句
        seen[d.u] = 1;
        const first = String(ck.t || "").replace(/\\s+/g, " ").trim().slice(0, 120);
        list.push({ t: d.t, u: d.u, kind: "", line: first, au: "", own: false, score: 1 });
      }
    } catch (e) {}
  }
  return list.sort((a, c) => c.score - a.score).slice(0, k);
}

'''
s = sub1(s, "function nbBlock(list) {", HELPER + "function nbBlock(list) {", "插入 nbrFor")

# ════════════════════════════════════════════════════════════════════
# 二、九道 SDE 工序块
# ════════════════════════════════════════════════════════════════════
TOOLS = r'''
/* ═══════════ SDE 工序（问WDS 独有；Claude/GPT 那边没有对应物）═══════════
   每道工序是一段**硬要求**，不是提示口吻：它规定这一轮必须交付哪几件东西、
   哪一件交不出就要明说交不出。刻意都带一条"做不到就直说"的出口——
   工序最怕的不是做不到，是假装做到了（那会静默地把一次没做的检测记成做过）。 */
const WDS_TOOL_KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "grid", "nine"];
const WDS_TOOLS = {
  iq: "【本轮工序 · 创新智商评分】把读者给你的文本（提问里贴的，或附件里的）当被评对象，按 SDE 学派创新智商五维逐维打分。"
    + "\n· S 显露度：有没有真显影出一个可辨认的新单位，还是只换了个说法。"
    + "\n· D 差异度：与**最近的那个既有说法**的距离——必须指名到具体篇目、学说或人，泛泛说「与传统不同」这一维不给分。"
    + "\n· E 纠缠度：跨了几界、几学科。只在本学科里打转的，这一维封顶。"
    + "\n· I 内部一致：三大方程代得进去吗；有没有把动词冻成名词、把开着的口封成圆（自我封顶）。"
    + "\n· F 可证伪：给不出自证伪条件的，这一维直接零分。"
    + "\n参照带：≤110 专业话语生产者 · 130 有真判断 · 140 资深学者（也是本站录取线）· 150 以上典范级。"
    + "\n输出：五维各一行（分数 ＋ 一句为什么是这个分 ＋ 要加分得补什么）→ 总分与层级 → 三条最短提升路径（每条说清补哪一维、怎么补）。"
    + "\n每一维都要附一句「若 X 成立，本维应降到 Y」——分数必须可被反驳。不要给安慰分；材料不足以评分就说不足以评，并指出缺哪一类材料。",

  three: "【本轮工序 · 三视角误差互消】同一个问题分三遍答，不许合并、不许互相引用："
    + "\n① 只从 S（显露）看：它显影出来的可辨认单位是什么，边界在哪，到哪一步才算成形。"
    + "\n② 只从 D（差异序列）看：它从什么差异里长出来，路径经过哪几步，哪一步不可逆。"
    + "\n③ 只从 E（特征纠缠）看：它与哪些环境、哪几界、哪些别的系统缠在一起，抽掉哪一根它就散。"
    + "\n④ 三视角互相校正：**必须真指出**其中两个视角看错或看漏了什么（不许说三个都对），再给一句三者互消后剩下的判断。"
    + "\n⑤ 一句话：这个判断最脆的一环在哪。",

  motif: "【本轮工序 · 母题打造】把手上的材料（本场对话 ＋ 附件里的全部篇目）压成**一条母题**。"
    + "\n母题不是主题：主题是名词短语（「论自由」），母题是一句反直觉、可被反驳的判断。"
    + "\n工序：① 动词扫描——列出各篇反复共绕的**动词族**（不是名词）；② 用动词族凝出 2–3 条候选母题；"
    + "\n③ 逐篇校验——每一篇贴不贴这条母题、贴在哪一句上；贴不上的单独列出，并判定是那一篇偏了还是母题太窄；"
    + "\n④ 定稿一条，二十五字以内；⑤ 给出这条母题的可证伪条件。"
    + "\n材料本就撑不起一条母题时，直说撑不起，并指出还缺哪一类材料——别用一句漂亮话糊过去。",

  nbr: "【本轮工序 · 近邻检测】这一轮的交付里必须有单独一节「近邻检测」，否则算没做完。"
    + "\n① 站内：对下面给出的近邻名单**逐条**交代——那一篇已经说到哪一步，你这次的判断与它的分离线在哪；划不出分离线的，直接说明本次判断与它重复，不要另起新名。"
    + "\n② 库外：另外点名**至少三个**站外的既有工作，每个都要给全四件——出处（作者＋年份或《作品》）、它说到哪一步、分离线、**一条判决性对照预测**（若某观测结果为 X，则它对而你错）。"
    + "\n③ 本节开头写一行「本文所属学科：XXX」，每个库外近邻的出处后紧跟「（学科：XXX）」。三个近邻**不许全挤在本文同一个学科里**，至少一个跨出去。"
    + "\n④ 名单里没有、但你知道确实更近的篇目，也要主动补进来。凑不满三个就说只找到几个，不要编出处——编出来的近邻比不做检测更坏。",

  rename: "【本轮工序 · 改姓】把读者给的文字改写成**目标学科的母语**。读者没说要投哪个学科，就先用一句话问清，再动手。"
    + "\n硬规矩：① 成品里**零 SDE 术语**——显露、差异序列、特征纠缠、发生学、三界、宫格、成熟态、底盘…… 一个都不许出现，注释与图题里也不许；"
    + "\n② 每处术语换成该学科本来就有的说法，换不掉的就改写整句，不许硬造；"
    + "\n③ 不许换皮不换骨：改完锋利度不能降、判断不能变软，不能变成一句正确的废话；"
    + "\n④ 输出两栏——改后的正文，加一张对照表（原说法 → 换成什么 → 为什么这个学科的人会认这个说法）。"
    + "\n⑤ 自查一遍：把成品交给该学科的同行看，他会不会觉得这是外人写的？会的话指出是哪一句露了口音。",

  gap: "【本轮工序 · 缝隙扫描与填缝】"
    + "\n① 先用三大方程与六路径把材料读一遍，指出它已经说到哪一步；"
    + "\n② 指认**缝隙**：它没能说、说不下去、或自相矛盾的那一处。缝隙不是「还可以进一步研究」，是结构上缺了一个东西才接不上——说清缺的是什么；"
    + "\n③ 为这个缝隙**发明一个新概念**去填它：给名字、一句定义、成立条件、可证伪条件；"
    + "\n④ 说清这个新概念与最近的既有概念的分离线（指名到人或篇目）；"
    + "\n⑤ 若这道缝隙其实已经被别人填过，直说，并指出谁填的、填得哪里不够——发明一个已有的概念是这道工序最大的失败。",

  collide: "【本轮工序 · 三篇碰撞】从站内资料里挑**三篇分属不同领域、且观点互相矛盾**的篇目（不是三篇互相支持的）。"
    + "\n① 先把三对矛盾逐对写出来：A 要什么 vs B 要什么，矛盾点是哪一句对哪一句；"
    + "\n② 再撞出一个**任何一篇单独看都看不到**的判断——它必须是三者共享的那个前提被拆穿的结果，不是三者的平均、也不是三者的综述；"
    + "\n③ 说清这个判断为什么非要三篇同时在场才出得来；"
    + "\n④ 文末列出三篇篇名与站内链接。"
    + "\n站内资料里凑不出互相矛盾的三篇时，直说凑不出、说明手上这几篇是彼此支持的，别硬凑一个假矛盾。",

  grid: "【本轮工序 · 27 宫格定位】把这件事放进 SIO 27 宫格："
    + "\n① C（内容）⊗ M（方法）⊗ V（价值）三轴各落哪一格，为什么是这一格；"
    + "\n② O 一号位（客体）、I 二号位（互动）、S 三号位（主体）分别是谁；"
    + "\n③ 中心位现在轮转到哪一位，凭什么判断是它；"
    + "\n④ 若中心位轮到另一位，这件事会变成什么样——这一条要具体到能被反驳；"
    + "\n⑤ 三号位是最后才显影的：在这件事里，它显影了没有？没有的话，卡在哪一步。"
    + "\n某一轴其实定不进任何一格时，直说定不进，并指出是这件事还没成形，还是这一轴在这里根本用不上——硬填一格比留空更坏。",

  nine: "【本轮工序 · 九宫格取三格】从九个视角里**抽三个不同的格**，只抽三个，不要九个都上："
    + "\nS1 对比/变化/分布 · S2 粒子/波/场 · S3 真/善/美 · D1 创造/自由/幸福 · D2 十步全程 · D3 三最小 · E1 理念/现实/自我 · E2 符号/逻辑/数学 · E3 内能/动能/势能。"
    + "\n每格：先用**完全不带术语的话**问一个问题（读者能听懂的那种问法），再自己答两三句。"
    + "\n最后一段：把三格撞成一条判断——三格都在场才成立的那一句。哪一格对这个问题其实用不上，就说用不上，换一格。"
};
// 工序是流程要求，不改人格：仍是王德生本人在说话，只是这一轮必须交付这几件东西。
function wdsToolSys(tool) {
  const b = WDS_TOOLS[tool];
  if (!b) return "";
  return "\n\n" + b + "\n（工序只管这一轮要交付什么，不改你的口吻：仍然直接、犀利、说人话，不要复述工序名、不要把小标题写成「工序①」。）";
}
'''
s = sub1(s, "function WDS_CHAT_SYS(reflect, SDEM, siteCtx, webCtx, deep, docCtx, about, lang, docNote) {",
         TOOLS + "\nfunction WDS_CHAT_SYS(reflect, SDEM, siteCtx, webCtx, deep, docCtx, about, lang, docNote, tool) {",
         "WDS_CHAT_SYS 签名加 tool")
s = sub1(s, '''    + (deep ? SDE_METHOD_BLOCK : "")''',
         '''    + (deep ? SDE_METHOD_BLOCK : "")
    + wdsToolSys(tool)''', "system 拼入工序块")

# ════════════════════════════════════════════════════════════════════
# 三、chat 处理器：收 tool、近邻工序取真名单、按工序调预算
# ════════════════════════════════════════════════════════════════════
s = sub1(s, '''      const lang = b.lang === "en" ? "en" : "zh";                 // 界面语言：决定用哪种语言作答''',
         '''      const lang = b.lang === "en" ? "en" : "zh";                 // 界面语言：决定用哪种语言作答
      // SDE 工序：白名单校验，认不出的一律当没选（绝不把读者传来的字符串拼进 system）
      const tool = WDS_TOOL_KEYS.indexOf(String(b.tool || "")) >= 0 ? String(b.tool) : "";''',
         "chat 收 tool")

# 碰撞工序要多看几篇站内文章，否则挑不出互相矛盾的三篇
s = sub1(s, '''              const _lrC = await lightRetrieve(env, url, q, expTerms, deep ? 30 : 20, 1600, { pick: deep ? 28 : 18 });''',
         '''              const wide = deep || tool === "collide";   // 碰撞要在更宽的面上挑，才可能凑出互相矛盾的三篇
              const _lrC = await lightRetrieve(env, url, q, expTerms, wide ? 30 : 20, 1600, { pick: wide ? 28 : 18 });''',
         "collide 加宽检索")

# 这一行在 chat 与 article-sde 两处一模一样（旧教训），必须连同它下面 chat 独有的 SDEM 行一起做锚
s = sub1(s, '''            let reflect = ""; try { reflect = await ensureReflect(env, url, rvendor, VC, KEY); } catch (e) {}
            const SDEM = "\\n\\nSDE 骨架''',
         '''            // 近邻工序：把真名单前置到 system（放在语料之前，否则会被两万字语料埋掉）。
            // 取不到就发 nbrfail 让前端如实说一句——静默失败等于把没做的检测记成做过了。
            let nbrCtx = "";
            if (tool === "nbr") {
              try {
                const nl = await nbrFor(env, url, q, 10, "", true);
                if (nl && nl.length) { nbrCtx = nbBlock(nl); controller.enqueue(_sseBytes({ t: "nbr", v: nl.map((x) => ({ t: x.t, u: x.u, au: x.au || "", own: !!x.own })) })); }
                else controller.enqueue(_sseBytes({ t: "nbrfail", v: "empty" }));
              } catch (e) { controller.enqueue(_sseBytes({ t: "nbrfail", v: "error" })); }
            }
            let reflect = ""; try { reflect = await ensureReflect(env, url, rvendor, VC, KEY); } catch (e) {}
            const SDEM = "\\n\\nSDE 骨架''',
         "近邻工序取真名单")

s = sub1(s, '''            const sys = WDS_CHAT_SYS(reflect, SDEM, ctxText, webCtx, deep, docCtx, about, lang, docNote);''',
         '''            const sys = WDS_CHAT_SYS(reflect, SDEM, (nbrCtx ? nbrCtx + "\\n" : "") + ctxText, webCtx, deep, docCtx, about, lang, docNote, tool);''',
         "system 前置近邻名单")

# 工序产出比闲聊长：非满功率档给宽一点；满功率档**仍然守 6000**（满功率必配有界预算，这条不许动）
s = sub1(s, '''body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: deep ? 6000 : 2600, messages })) });''',
         '''body: JSON.stringify(wdsTopBody(VC, { model: VC.model, stream: true, max_tokens: deep ? 6000 : (tool ? 4000 : 2600), messages })) });''',
         "工序档 max_tokens")

with io.open(W, "w", encoding="utf-8") as f:
    f.write(s)
print("worker tools patch ok — bytes:", len(s))
