#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatSDE 第 15 道工序「发生场」（2026-08-28 王德生令）

「海选 → 闸门 → 顶住 → 真跑」结合路线的第一棒：不回答问题，先布置一场发生——
摆料（站内语料＋跨学科家底＋占位者名单）→ 上张力（对阵＋共有前提）→ 出候选
（5–8 条四行格式的候选分辨：候选/分岔/作废/张力源）。只生不判：不许排名、不许自评、
允许自淘。四行行首是给下一棒（过闸）预留的机检面。

七处编辑（幂等；逐条 assert 锚点唯一）：
  A  worker  WDS_TOOL_KEYS 白名单 + "genesis"
  B  worker  WDS_TOOLS 加 genesis 工序正文（插在对象最前，nine 保持末位——
             sim_wds_sde_tools 的 nine 正则钉的是「nine 到 \\n};」）
  C  worker  占位者链触发：旁挂 wantNbrG = wantNbr || genesis（不并进原行——
             sim_chatsde_forge:196 与 sim_distill_nbr:72 按原样钉着那行的形状）
  D  前端    TOOLS 数组加条目（cmd：发生场/genesis/布场）
  E  前端    中/英文案 tlGenesis / tlGenesisS
  G  护栏    sim_wds_sde_tools.js 的 KEYS 表 + "genesis"（它按 KEYS.length 数
             「本轮工序」的道数，不带上它当场红）

分身档（lang/liter/edu/health/math/comp）**不给这一道**：各档 tools 白名单一字不动，
wdsToolSys 的 prof.tools 闸自然挡住；前端 PROFILE.tools 过滤同理。改姓版（WDS_TOOLS_LANG）
不加——分身没有这道，改姓版无处可挂。

跑完本脚本后必须：node --check 两个文件 → node tools/sim_chatsde_genesis.js →
相邻护栏全绿 → python3 tools/bump_wds_mode.py（改了 wds-mode.js 必 bump）。
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'src/worker.js')
M = os.path.join(ROOT, 'public/wds-mode.js')
G = os.path.join(ROOT, 'tools/sim_wds_sde_tools.js')

changed = []


def sub1(text, old, new, tag, done_mark):
    if done_mark in text:
        print('  · %s 已打过，跳过' % tag)
        return text
    n = text.count(old)
    assert n == 1, '锚点 %s 命中 %d 次（应为 1）' % (tag, n)
    changed.append(tag)
    return text.replace(old, new, 1)


# ═══════════════════ worker.js ═══════════════════
h = io.open(W, encoding='utf-8').read()

# A · 白名单
h = sub1(
    h,
    'const WDS_TOOL_KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "forge", "what", "how", "why", "grid", "nine", "map"];',
    'const WDS_TOOL_KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "forge", "what", "how", "why", "grid", "nine", "map", "genesis"];',
    'A·白名单', '"genesis"];')

# B · 工序正文（插在 WDS_TOOLS 最前；nine 必须留在末位）
GENESIS_ENTRY = r'''  /* ═══ 发生场（2026-08-28 王德生令；「海选→闸门→顶住→真跑」接力的第一棒：布置发生）═══
     这一道不回答问题——摆料→上张力→出候选，交一批四行格式的候选分辨。
     ⚠ 三条设计约束，改之前先读：
       ① 只生不判：不许排名、不许自评——排名是锦标赛那套的事，判交给下一棒（过闸）；
       ② 四行行首（候选/分岔/作废/张力源）是给下一棒预留的机检面，动了下游接不上；
       ③ 允许自淘且不惩罚——敢淘汰自己的批次才可信（同〔交账〕敢写「无」一个道理）。
     对手名单：wantNbrG 已把这一档接进占位者专用链（与评分共用 nbrChain，第五刀）；
     没召回名单时按第五刀同款纪律走〔未核验〕，绝不许「据我所知尚无人提出」。 */
  genesis: "【本轮工序 · 发生场】这一轮**不回答读者的问题**——你的活是给这一问布置一场发生，交出一批候选分辨。只生不判，三步一步不许省：\n"
    + "**一 · 摆料**：把家底摆上台——《站内资料》里碰过这一问的说法；你记忆库里**跨至少两个学科**的已有说法（至少三家，逐家一句说清它讲到哪儿为止）；《站外对手》名单里的占位者（有名单就至少请两位上台）。宁缺勿造：想不起来只说明没想起来，不等于没人说过。没有《站外对手》名单，这一步就明写一行「站外对手：未核验」，后面所有分岔按〔未核验〕口径写，全文不许出现「据我所知尚无人提出」。\n"
    + "**二 · 上张力**：不许把摆出的说法排成清单——摆成**对阵**：挑真打架的两三对，逐对指出它们在哪一点上**不能同时成立**；再逼一句：这几家**共同假定了什么**（那句念给几家听、家家都说「这还用说吗」的话）。摆不出真对阵就直说「这一题只有并列、没有对阵」，候选随之减到两三条，不许硬凑。\n"
    + "**三 · 出候选**：交出 5 条候选分辨（对阵撑得起可到 8 条，撑不起就少出，宁缺勿滥）。每条固定四行，行首照抄：\n"
    + "候选：X 不是 Y，而是 Z（承重句要能被原样复述；新说法当场一句话定义）\n"
    + "分岔：与家底里的哪家说法、从哪一步分岔（有《站外对手》名单时，至少两条候选的这一行要对着名单里的人说）\n"
    + "作废：若观察到什么，此条作废（给不出就写「给不出」，不许拿怎么都对的话充数）\n"
    + "张力源：它结算的是第二步哪一场对阵（没有对阵就写「无对阵·仅并列」）\n"
    + "**三条禁令**：① 不许给候选排名、标星或说哪条最好——判是下一棒的事；② 不许自评分数或写「本条创新度高」这类评语；③ 候选之间不许是同一条分辨换几种说法。\n"
    + "**允许自淘**：哪条写完发现只到复述，就在它的候选行末尾标「〔自淘：只到复述〕」并保留全文——敢淘汰自己的批次才可信，凑数凑满的批次一文不值。\n"
    + "〔交账〕行照常交，两处按这一档改：作废条件抄候选里最硬的那一句；「新在」写成批账「N 条候选（自淘 M、带作废 K）」。",

'''
h = sub1(h, 'const WDS_TOOLS = {\n', 'const WDS_TOOLS = {\n' + GENESIS_ENTRY,
         'B·工序正文', '\n  genesis: "【本轮工序 · 发生场】')

# C · 占位者链触发（旁挂，不动被两份护栏钉住的那一行）
OLD_C = '''            const wantNbr = (rs && rs.forge && FORGE_NBR_STAGES[rs.i | 0]) || tool === "iq";
            if (wantNbr) {'''
NEW_C = '''            const wantNbr = (rs && rs.forge && FORGE_NBR_STAGES[rs.i | 0]) || tool === "iq";
            /* genesis（发生场）：对手名单与评分/产线共用第五刀那条占位者专用链（nbrChain）。
               旁挂一行、不并进上一行——sim_chatsde_forge:196 与 sim_distill_nbr:72
               按原样钉着上一行的形状；覆盖不足的〔未核验〕纪律写在工序正文里。 */
            const wantNbrG = wantNbr || tool === "genesis";
            if (wantNbrG) {'''
h = sub1(h, OLD_C, NEW_C, 'C·占位者链', 'const wantNbrG = wantNbr || tool === "genesis";')

io.open(W, 'w', encoding='utf-8').write(h)

# ═══════════════════ public/wds-mode.js ═══════════════════
f = io.open(M, encoding='utf-8').read()

# D · TOOLS 数组
f = sub1(
    f,
    '    { k: "map", n: "tlMap", s: "tlMapS", cmd: ["结构图", "map", "导图"] }\n  ];',
    '    { k: "map", n: "tlMap", s: "tlMapS", cmd: ["结构图", "map", "导图"] },\n'
    '    { k: "genesis", n: "tlGenesis", s: "tlGenesisS", cmd: ["发生场", "genesis", "布场"] }\n  ];',
    'D·前端清单', '{ k: "genesis"')

# E · 文案（中/英）
f = sub1(
    f,
    'tlMap: "结构图", tlMapS: "把这一问里的结构画成图（落在右侧画布里），并说清哪条边最承重",',
    'tlMap: "结构图", tlMapS: "把这一问里的结构画成图（落在右侧画布里），并说清哪条边最承重",\n'
    '      tlGenesis: "发生场", tlGenesisS: "不答题，先布一场发生：摆料、上张力，交出五到八条自带分岔与作废条件的候选分辨",',
    'E·中文文案', 'tlGenesis: "发生场"')
f = sub1(
    f,
    'tlMap: "Structure map", tlMapS: "Draw the structure behind this question (renders on the canvas) and say which edge carries the weight",',
    'tlMap: "Structure map", tlMapS: "Draw the structure behind this question (renders on the canvas) and say which edge carries the weight",\n'
    '      tlGenesis: "Genesis field", tlGenesisS: "Stage a genesis instead of answering: lay out the stock, set up the clash, deliver 5-8 candidate distinctions each with its fork and kill condition",',
    'E·英文文案', 'tlGenesis: "Genesis field"')

io.open(M, 'w', encoding='utf-8').write(f)

# ═══════════════════ tools/sim_wds_sde_tools.js ═══════════════════
g = io.open(G, encoding='utf-8').read()
g = sub1(
    g,
    'const KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "forge", "what", "how", "why", "grid", "nine", "map"];',
    'const KEYS = ["iq", "three", "motif", "nbr", "rename", "gap", "collide", "forge", "what", "how", "why", "grid", "nine", "map", "genesis"];',
    'G·护栏KEYS', '"genesis"];')
io.open(G, 'w', encoding='utf-8').write(g)


# ═══ 追补（首轮相邻护栏跑出两处数量红之后）═══════════════════════════
# forge 护栏是「文案-件数对账」：worker 名录正文写着「十四件**单轮工序**」，键数也须 14。
# 加第 15 道 ⇒ 名录正文、行 890 注释、名录枚举、forge 护栏、mode_v2 菜单计数五处随之走。
h = io.open(W, encoding='utf-8').read()
h = sub1(h, '（十四件工序＋十八道产线', '（十五件工序＋十八道产线',
         'H1·注释件数', '（十五件工序＋十八道产线')
h = sub1(h, '你手上有十四件**单轮工序**', '你手上有十五件**单轮工序**',
         'H2·名录件数', '你手上有十五件**单轮工序**')
h = sub1(h, '｜**/结构图** 画成 mermaid 图',
         '｜**/结构图** 画成 mermaid 图｜**/发生场** 不答题：摆料、上张力，交 5–8 条自带分岔与作废条件的候选分辨（只生不判，判交下一棒）',
         'H3·名录枚举', '**/发生场** 不答题')
io.open(W, 'w', encoding='utf-8').write(h)

FG = os.path.join(ROOT, 'tools/sim_chatsde_forge.js')
g2 = io.open(FG, encoding='utf-8').read()
g2 = sub1(g2,
    'ok("单轮工序仍是十四件，且改称「件」以免与道次混淆",\n'
    '  /十四件\\*\\*单轮工序\\*\\*/.test(W) && (W.match(/const WDS_TOOL_KEYS = \\[([^\\]]*)\\]/) || ["", ""])[1].split(",").length === 14);',
    'ok("单轮工序与名录文案对账（2026-08-28 加发生场后十五件），且仍称「件」以免与道次混淆",\n'
    '  /十五件\\*\\*单轮工序\\*\\*/.test(W) && (W.match(/const WDS_TOOL_KEYS = \\[([^\\]]*)\\]/) || ["", ""])[1].split(",").length === 15);',
    'I·forge对账', '十五件\\*\\*单轮工序')
io.open(FG, 'w', encoding='utf-8').write(g2)

MV = os.path.join(ROOT, 'tools/sim_wds_mode_v2.js')
g3 = io.open(MV, encoding='utf-8').read()
g3 = sub1(g3,
    '  ok(!!tlm && tlm.querySelectorAll("button").length === 15, "工序菜单十四道＋「不用工序」共十五项，实得 " + (tlm ? tlm.querySelectorAll("button").length : 0));',
    '  /* 跟着 TOOLS 走，别写死数量——加一道工序就得回来改数字（sim_wds_sde_tools 同款纪律；\n'
    '     2026-08-28 加「发生场」时这里红过一次）。 */\n'
    '  const _tlN = (src.slice(src.indexOf("var TOOLS = ["), src.indexOf("\\n  ];", src.indexOf("var TOOLS = ["))).match(/\\{ k: "/g) || []).length;\n'
    '  ok(_tlN >= 14, "TOOLS 清单抠得到（>=14 道），实得 " + _tlN);\n'
    '  ok(!!tlm && tlm.querySelectorAll("button").length === _tlN + 1, "工序菜单 " + _tlN + " 道＋「不用工序」共 " + (_tlN + 1) + " 项，实得 " + (tlm ? tlm.querySelectorAll("button").length : 0));',
    'J·mode_v2跟单', '_tlN + 1')
io.open(MV, 'w', encoding='utf-8').write(g3)


# ═══ 顺手修：sim_wds_platform 三条陈旧红（基线就红，与本刀无关；同 08-23 修 sim_wds_triad 的先例）═══
# 病理：08-22 分身分流把注入行改成三元式，拼写钉脱靶；旧界标「/* ═══ SDE 工序」消失，
# indexOf 回 -1 ⇒ seg 吞掉整个文件尾，把邻段的 /taste/assets/ /all/ 当成名录路径。按行为重钉。
PL = os.path.join(ROOT, 'tools/sim_wds_platform.js')
g4 = io.open(PL, encoding='utf-8').read()
g4 = sub1(g4,
    'const seg = i < 0 ? "" : W.slice(i, W.indexOf("\\n/* ═══════════ SDE 工序", i));',
    '/* 旧界标已在后续改版中消失，indexOf 回 -1 会让 seg 吞到文件尾（2026-08-28 抓出）。\n'
    '   改钉下一个常量 LANG_PLATFORM_BLOCK 的定义行——它就是本块的真实下边界；照 -1 纪律先断「在」。 */\n'
    'const _segEnd = W.indexOf("\\nconst LANG_PLATFORM_BLOCK", i);\n'
    'const seg = (i < 0 || _segEnd < 0) ? "" : W.slice(i, _segEnd);',
    'K1·seg边界', 'const _segEnd = W.indexOf')
g4 = sub1(g4,
    'ok(/\\+ SDE_TRIAD_BLOCK\\s*\\n\\s*\\+ SDE_PLATFORM_BLOCK/.test(W), "紧跟三类问题块无条件拼进去");',
    'ok(/\\(\\(prof && prof\\.term\\) \\? LANG_TRIAD_BLOCK : SDE_TRIAD_BLOCK\\)\\s*\\n\\s*\\+ \\(\\(prof && prof\\.term\\) \\? LANG_PLATFORM_BLOCK : SDE_PLATFORM_BLOCK\\)/.test(W),\n'
    '   "紧跟三类问题块拼进去（08-22 起走分身三元式：本体档拿原版、分身档拿改姓版，仍是无条件）");',
    'K2·三元式重钉', '本体档拿原版、分身档拿改姓版')
g4 = sub1(g4,
    'const inj = W.indexOf("+ SDE_PLATFORM_BLOCK");\n'
    'ok(cs > 0 && cs < iq && iq < inj, "注入点在 WDS_CHAT_SYS 内且在 iq 改道之后（评分者不装名录）");',
    'const inj = W.indexOf(": SDE_PLATFORM_BLOCK)");\n'
    'ok(inj > 0, "注入表达式找得到（-1 防线：先断在，再比序）");\n'
    'ok(cs > 0 && cs < iq && iq < inj, "注入点在 WDS_CHAT_SYS 内且在 iq 改道之后（评分者不装名录）");',
    'K3·注入点重钉', '先断在，再比序')
io.open(PL, 'w', encoding='utf-8').write(g4)


g4b = io.open(PL, encoding='utf-8').read()
g4b = sub1(g4b,
    'const paths = Array.from(new Set((seg.match(/\\/[a-z0-9][a-z0-9\\-\\/]*\\//g) || [])));',
    '/* 只反查「送人去的页面路径」。目录后面紧跟文件名的（/taste/assets/lang-neigong.txt 这类\n'
    '   维护注释里的资产引用）不是页面，不在此列——2026-08-28 抓出：老写法把文件路径截成目录前缀来反查。 */\n'
    'const _rawPaths = [];\n'
    'const _re = /\\/[a-z0-9][a-z0-9\\-\\/]*\\//g; let _m;\n'
    'while ((_m = _re.exec(seg))) {\n'
    '  if (!/^[a-z0-9_\\-]+\\.[a-z0-9]{2,5}\\b/.test(seg.slice(_m.index + _m[0].length))) _rawPaths.push(_m[0]);\n'
    '}\n'
    'const paths = Array.from(new Set(_rawPaths));',
    'K4·只查页面路径', 'const _rawPaths = [];')
io.open(PL, 'w', encoding='utf-8').write(g4b)

print('打上的补丁：%s' % (', '.join(changed) if changed else '（全部已打过，本次零改动）'))
print('下一步：node --check src/worker.js public/wds-mode.js && node tools/sim_chatsde_genesis.js')
