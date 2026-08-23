#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatSDE 追问建议 · 三件工具各出一问（2026-08-23 王德生令）

原来三条追问都走「六路径」，只是起手维度不同——三条其实是同一件工具的三种用法。
现在改成三件工具各出一条，且恰好落成 What / How / Why：

    What → 三大方程（S=F(D,E) / D=G(S,E) / E=H(S,D)）  问「它是什么关系、什么结构」
    How  → 六路径（S/D/E 的六种排列）                    问「怎么走、从哪下手」
    Why  → 三原理（D×E→S / S×E→D / S×D→E）             问「为什么会这样、为什么卡住」

这个对应不是我配的，是内功【四·每一答的工序】里原有的「起手按问题种类三选一」，
把它从答题侧搬到了提问侧：读者每点一次，就换一件工具、换一种问法。

幂等；逐条 assert 锚点唯一。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'src/worker.js')
M = os.path.join(ROOT, 'public/wds-mode.js')

h = io.open(W, encoding='utf-8').read()
changed = []


def sub1(text, old, new, tag, done_mark):
    if done_mark in text:
        print('  · %s 已打过，跳过' % tag)
        return text
    n = text.count(old)
    assert n == 1, '锚点 %s 命中 %d 次（应为 1）' % (tag, n)
    changed.append(tag)
    return text.replace(old, new, 1)


# ── 服务端：followSys / followUps 整段换掉 ───────────────────────────────
old_start = h.index('function followSys(prof) {')
old_end = h.index('\n\n// ===== 联网搜索（站外资料）=====')
old_block = h[old_start:old_end]
assert 'async function followUps' in old_block, '截取范围不对'

NEW_BLOCK = r'''/* 【三件工具各出一问】2026-08-23 王德生令：
   「每次问对后，应该都能生成三个问题：一个用三方程的某个来问，一个用六路径的某一条来问，
     一个用三原理的某个来问；一个 What、一个 How、一个 Why——把思考引向深入。」
   在此之前三条追问全走六路径，只是起手维度不同——三条其实是同一件工具的三种用法，
   读者点十次也只换过起手维度，没换过看事情的层。
   What/How/Why 与三件工具的对应不是新配的，是内功【四·工序】里原有的「起手按问题种类三选一」，
   现在把它从答题侧搬到提问侧：**每点一次就换一件工具**。 */
const SDE_EQUATIONS = "S=F(D,E) 显露态由差异与纠缠共同长成（拿到一个结论，就问它经什么差异路径、在什么土壤里长出来）｜"
  + "D=G(S,E) 差异路径由已成的显露态与土壤共同规定（问这条路为什么是这么走的、被什么定住了）｜"
  + "E=H(S,D) 纠缠土壤本身也是被显露态与路径改写出来的（问它站在什么上面、那片土壤怎么来的）";
const SDE_PRINCIPLES = "原理一 D×E 矛盾→S 改变（是什么张力把这个结果逼出来的，改完又回写了什么）｜"
  + "原理二 S×E 矛盾→D 改变（是什么逼得这条路径改了道）｜"
  + "原理三 S×D 矛盾→E 改变（是什么逼得整片土壤换了）";
/* 分身版（改姓纪律：对外产出零内部行话）。语言老师、小学老师看到「E=H(S,D)」只会关掉页面。
   三件工具的内在分工一字未动，只换它们在读者面前怎么自报家门。 */
const FOLLOW_EQ_LANG = "它是由什么长成的（这说法经什么用法、在什么场合长成现在这样）｜"
  + "这条路为什么这么走（是什么把它定成了现在这个走法）｜"
  + "它站在什么上面（这一整片环境本身是怎么来的）";
const FOLLOW_PR_LANG = "什么张力逼出了这个结果（改完之后又反过来改了什么）｜"
  + "什么逼得做法改了道（原来那条路走不下去了在哪）｜"
  + "什么逼得整个环境换了（不是某个人改的，是什么让它非换不可）";
const FOLLOW_KINDS = ["What", "How", "Why"];
const FOLLOW_KINDS_CN = ["是什么", "怎么做", "为什么"];

function followSys(prof) {
  const L = !!(prof && prof.term);          // 分身档（语言/健康等）：不许出现内部术语
  return (L ? "你是这场谈话的旁观者，也是引路人。" : "你是对话的旁观者，也是 SDE 的引路人。")
  + "看完一问一答，给读者三条自然的下一问。**三条必须各用一件不同的工具，恰好是一个 What、一个 How、一个 Why。**"
  + "\n\n【第一条 · What" + (L ? "" : " · 三大方程") + "】问的是「它是什么关系、什么结构」。三条里挑最能撬动这一答的一条：\n"
  + (L ? FOLLOW_EQ_LANG : SDE_EQUATIONS)
  + "\n\n【第二条 · How" + (L ? "" : " · 六路径") + "】问的是「怎么走、从哪下手」。六条里挑一条，尽量避开这一答已经走完的那条：\n"
  + (L ? FOLLOW_PATHS_LANG : SDE_PATHS)
  + "\n\n【第三条 · Why" + (L ? "" : " · 三原理") + "】问的是「为什么会这样、为什么卡在这儿」。三条里挑一条：\n"
  + (L ? FOLLOW_PR_LANG : SDE_PRINCIPLES)
  + "\n\n规矩：\n① 严格三行，第一行 What、第二行 How、第三行 Why，顺序不许换。"
  + "\n② 每行写成 `类型·工具名｜问句`（两个分隔符照抄：中点与竖线）。类型只写 What/How/Why 之一；"
  + "工具名照抄上面那一条的**开头几个字**，别自造、别写整句。"
  + "\n③ 问句 8–24 字，是读者真会问的一句话，**不是你想讲的下一段**；必须接着这一答的具体内容问，"
  + "不许是「能再详细讲讲吗」「有什么例子吗」这类放到哪一答都成立的万能句。"
  + "\n④ 三条要真的往下走一层，不许是同一个问题换三种说法。"
  + "\n⑤ 只输出三行，别的什么都不要，不编号、不解释。";
}

/* 解析抽成纯函数，就是为了能逐条单测（同 probeVerdict 那次的做法）。
   **必须宽容**：模型偶尔漏分隔符、多写编号、把类型写成中文。
   漏了就按行序补 What/How/Why——引导是增益，不能因为格式没对上就一条都不给。 */
function parseFollows(out, prof) {
  const L = !!(prof && prof.term);
  const PATHNAMES = L ? FOLLOW_NAMES_LANG
    : ["学科本体论分析", "配置与决策", "咨询与干预", "求助与困境", "社会分析", "综述与建制"];
  const TOOLS = (L ? [FOLLOW_EQ_LANG, FOLLOW_PATHS_LANG, FOLLOW_PR_LANG]
                   : [SDE_EQUATIONS, SDE_PATHS, SDE_PRINCIPLES])
    .map((s) => s.split("｜").map((x) => x.trim()));
  const rows = [];
  for (const line of String(out || "").split(/\n+/)) {
    const s = String(line).replace(/^[\s\d.、)\-*·]+/, "").trim();
    if (!s) continue;
    const bar = s.split(/[|｜]/);
    let head = "", qq = s;
    if (bar.length >= 2) { head = bar[0].trim(); qq = bar.slice(1).join("|").trim(); }
    qq = qq.replace(/^[\s:：]+/, "").trim();
    if (qq.length < 4 || qq.length > 40) continue;
    const i = rows.length;                       // 行序即 What/How/Why 的序，模型写错了也按序纠正
    if (i > 2) break;
    const kind = L ? FOLLOW_KINDS_CN[i] : FOLLOW_KINDS[i];
    // 工具名：先认模型写的（必须真在那一类的名单里），认不出就留空 —— 宁可不标，不许标错
    let tool = "";
    const seg = head.split(/[·•・\s]+/).filter(Boolean);
    for (const part of seg) {
      if (/^(what|how|why|是什么|怎么做|为什么)$/i.test(part)) continue;
      const hit = TOOLS[i].find((t) => t.indexOf(part) === 0 || part.indexOf(t.split(/[ （(]/)[0]) === 0);
      if (hit) { tool = hit; break; }
    }
    if (!tool && i === 1) { const p = PATHNAMES.find((n) => head.indexOf(n) >= 0); if (p) tool = p; }
    rows.push({ p: kind, q: qq, w: tool });
  }
  return rows.slice(0, 3);
}

async function followUps(VC, KEY, q, ans, lang, prof) {
  try {
    const sys = followSys(prof) + (lang === "en" ? "\n⑥ Write the three questions in English (keep the What/How/Why labels)." : "");
    // 短截止（WDS_FOLLOW_MS）：这一步跑在正文写完之后、同一个请求里，客户端要等 [DONE] 才收尾并挂出操作行。
    // 吃缺省 55 秒＝正文早写完了，读者却按不到 复制/继续/重答。它是配菜：晚了就不上，不许拖住正菜。
    // 预算 260→460：三行现在各多带一个工具名，260 会把第三行截在半句上（第三行正是 Why，最不该丢的那条）。
    const out = await llmText(VC, KEY, sys, "读者问：" + String(q).slice(0, 400) + "\n\nWDS 答：" + String(ans).slice(0, 2500) + "\n\n三行：", 460, WDS_FOLLOW_MS);
    if (!out) return [];
    return parseFollows(out, prof);
  } catch (e) { return []; }
}'''

h = sub1(h, old_block, NEW_BLOCK, '服务端 followSys/followUps 改造', '【三件工具各出一问】')
io.open(W, 'w', encoding='utf-8').write(h)

# ── 前端：工具名进 tooltip（加法式，老客户端照旧能用）───────────────────
m = io.open(M, encoding='utf-8').read()
old_tag = '''      if (p) { var tag = el("i", "pt", p); tag.title = t("pathTip"); b.appendChild(tag); }'''
new_tag = '''      // w = 这一条用的是哪件工具（三方程/六路径/三原理里的哪一条）。没有 w 就退回通用说明，
      // 老服务端只回 {p,q} 时行为一字不变。
      var w = (item && typeof item === "object") ? String(item.w || "") : "";
      if (p) { var tag = el("i", "pt", p); tag.title = w || t("pathTip"); b.appendChild(tag); }'''
m = sub1(m, old_tag, new_tag, '前端 tooltip 带工具名', 'var w = (item && typeof item === "object") ? String(item.w')
io.open(M, 'w', encoding='utf-8').write(m)

print('\n共改动 %d 处：' % len(changed))
for c in changed:
    print('  -', c)
