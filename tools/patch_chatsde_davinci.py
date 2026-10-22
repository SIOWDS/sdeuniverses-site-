#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatSDE · 第二十道单轮工序「达芬奇发生体」（2026-10-22 王德生令）

孩子由情激发的奇思妙想 → SDE 处理（补维连线、守奇）→ 新的艺术脚本
→ 交给大模型显露成漫画／动画／视频。儿童艺术达芬奇发生学。

按 sim_tool_registry.js 的规矩「加工序＝三处同时加」，本脚本一次落五处：
  后端 src/worker.js：① WDS_TOOL_KEYS 白名单 ② WDS_TOOLS 正文 ③ TOOL_SPEC 机检面 ④ 平台名录一行
  前端 public/wds-mode.js：⑤ 中英标签各一对 ＋ TOOLS 菜单一条
幂等：已打过就跳过。跑法：python3 tools/patch_chatsde_davinci.py
"""
import io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, "src", "worker.js")
F = os.path.join(ROOT, "public", "wds-mode.js")


def rd(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()


def wr(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def sub1(s, old, new, what):
    assert old in s, "锚点没找到：" + what
    assert s.count(old) == 1, "锚点不唯一（%d 处）：%s" % (s.count(old), what)
    return s.replace(old, new, 1)


w = rd(W)
f = rd(F)
if "  davinci: \"【本轮工序 · 达芬奇发生体】" in w:
    print("已打过，跳过。")
    sys.exit(0)

# ════════ ① 白名单 ════════
w = sub1(w, '"map", "genesis"];', '"map", "genesis", "davinci"];', "WDS_TOOL_KEYS 末尾")

# ════════ ② 工序正文（挂在 genesis 正文之后、map 注释之前）════════
DAVINCI = r'''
  /* ═══ 达芬奇发生体（2026-10-22 王德生令；儿童艺术达芬奇发生学）═══
     孩子一句由情激发的奇思妙想 → SDE 补维连线（三方程/六路径/123）→ 原创艺术脚本 → 显露工坊。
     ⚠ 四条设计约束，改之前先读：
       ① 守奇：孩子原话里那个「不合理的错位」是种子，不是错误。补维是给它长出 S/D/E 三条腿，
          不是把它改合理——「天空在洗澡」被改成「这是水循环」＝把种子煮熟了（#501：常＝被立成统一规矩）。
       ② 由情激发：情只记事实（孩子当时在哪、看见什么、说话时什么样子），不许替孩子做心理解释。
       ③ 未成年人红线：不问不记孩子真名、学校、住址、照片；不画真实儿童肖像；角色一律原创，不许借现成 IP。
       ④ 艺术门 ≠ 知识门：脚本是艺术交火（#125），验法是孩子回写；不许把脚本当事实教给孩子。 */
  davinci: "【本轮工序 · 达芬奇发生体】读者递来的是一个孩子的奇思妙想（通常由家长或老师转述）。这一轮**不讲道理、不纠正、不科普**——你的活是把这一句由情激发的奇想，用 SDE 方法论长成一个**原创艺术脚本**，再交出能直接拿去显露的稿子。五步一步不许省，标题照抄：\n"
    + "**一 · 采情**：\n"
    + "原话：用引号一字不改地抄孩子的原话（转述者改过的，标〔转述〕；没有原话就直说没有，先问）。\n"
    + "情境：只记事实——当时在哪、在做什么、看见/听见了什么、说这句话时的样子（笑着、皱眉、跑过来……）。**不许**写「这反映了孩子的某种心理」之类解释。\n"
    + "情源：这句话是被什么情激发的，用转述者给的事实写一句；转述里没有情的痕迹，就明写「情源：未给」并在第五步追问，**不许编一个情**。\n"
    + "**二 · SDE 处理（补维连线、守奇）**：\n"
    + "奇核：一句话指出原话里那个**不合常理的错位**（如「天空」与「洗澡」被缠在了一起）——这一句是整轮的种子，后面任何一步都不许把它改合理。\n"
    + "S（显露）：孩子看见/说出的那个画面，一句。D（差异序列）：这个画面之前是什么、之后会变成什么，写成 3–5 步的变化序列——这是情节的骨。E（特征纠缠）：哪两三样东西被孩子缠在一起，各自带进来什么特征。\n"
    + "三方程各一句：S=F(D,E) 这个画面怎么由变化和纠缠撑起来；D=G(S,E) 变化为什么只能这样走；E=H(S,D) 纠缠为什么非这几样不可。\n"
    + "路径：孩子是从哪一维起步的（多半从 E 或 S 起），据此定六路径之一作为叙事次序，写明「起于 X → Y → Z」。\n"
    + "123：找出这个奇想世界里 D 与 E 的那一处矛盾（故事的冲突）→ 显露怎样改变来化解 → 改变之后回写到哪里（结尾的余韵落在哪）。\n"
    + "缺维：三维里孩子没给的那一维，你补上的部分逐条标〔补维〕，并说清从奇核的哪一点长出来；补不出就标〔缺维·待孩子〕，不许硬编。\n"
    + "**三 · 艺术脚本**：\n"
    + "角色卡：2–3 个**原创**角色，每个写名字、外形三个特征、性格一句、来自奇核的哪一部分。\n"
    + "世界规则：这个世界里什么是真的（1–3 条，必须从奇核推出，例如「云是天空的毛巾」）。\n"
    + "情节节拍：按第二步的路径次序写 4–6 拍，每拍一行，标出它对应 D 序列的第几步。\n"
    + "分镜：4–8 格的表，列为 格号｜画面｜台词/旁白｜声音｜情绪。画面栏必须写得能画（景别、主体、动作、颜色），不许只有台词。\n"
    + "情绪曲线：一行，写清从哪个情起、在哪一格最高、落在哪个情。\n"
    + "**四 · 显露工坊**：\n"
    + "① 一个 ```html 围栏代码块：四格（或六格）漫画示意稿，纯内联 SVG＋CSS（可带轻微 CSS 动画），不引外链、不用位图；造型简单、色彩明亮、每格下一行台词。它是示意稿，画不像不要紧，结构对就行。\n"
    + "② 图像提示词：每格一条，中英各一行，写主体、动作、景别、光线、色彩与画风（画风只用通用描述，如「水彩绘本风」「蜡笔涂鸦风」；**不许**写在世艺术家姓名、动画公司或任何现成角色名）。\n"
    + "③ 视频镜头脚本：每镜不超过 8 秒，写镜头运动、画面变化与声音；最后一镜给出回写的余韵。\n"
    + "明说一句：本轮交的是脚本与示意稿；真正的插画、动画与视频需要另交图像/视频生成模型去显露。\n"
    + "**五 · 回写**：\n"
    + "给孩子的三个问题：两个选择题（每题两三个选项，都从奇核长出来，例如「天空洗完澡，是用云擦干，还是用风吹干？」）＋一个开放题（「它洗完澡想去做什么？」）。还要追问的事实（情源未给、缺维·待孩子）一并放这里问转述者。\n"
    + "空白格：在分镜里留一格「孩子来画/来说」，写明孩子答完后它接进第几拍、怎样改写后面的节拍。\n"
    + "**五条红线**：① 不问、不记、不写孩子的真名、学校、住址、长相与照片，角色不许以真实儿童为原型；② 角色、世界、画风一律原创，**不许**出现任何现成卡通/影视/游戏角色或品牌；③ 内容适龄：不写恐怖、暴力、浪漫情节；孩子的情若是害怕或难过，故事要给出安全的出口，但不许说教；④ 结尾**不许**加「这个故事告诉我们……」的道理；⑤ 孩子的奇想若碰到真实世界的知识（如下雨的成因），只能在全文最后另起一行，标〔知识门〕用一两句准确说明，**不许**用它去纠正或改写脚本——脚本是〔艺术门〕。\n"
    + "〔交账〕行照常交，两处按这一档改：「新在」写成「奇核：……（守住了／在第 N 步被磨平了）」；作废条件写「孩子回写时若说『不是这样的』，以孩子为准，回到第二步重做」。"
    + "\n\n**这样写＝没做**：原话被改通顺了／奇核被解释成科学道理（种子被煮熟了）／角色是现成的卡通形象换了个名字／情节套成「遇到困难—朋友帮忙—学到道理」的通用模板（#501 说的「常」：被立成统一规矩）／分镜只有台词没有画面／替孩子写了一段心理分析／结尾在讲道理／没有给孩子留回写的格子。"
    + "\n**守奇自检**（交账前做一次）：把第三、四步每一处改编对着奇核念一遍——哪一处让奇核变「合理」了，改回去，并在交账里写明改了哪一处。"
    + "\n长度约 2200 字（不含 html 代码块）。",
'''
w = sub1(w,
         "\n\n  // 结构图：画出来，不是描述。产出一个 mermaid 块",
         DAVINCI + "\n  // 结构图：画出来，不是描述。产出一个 mermaid 块",
         "WDS_TOOLS 中 map 注释（davinci 挂在其前）")

# ════════ ③ TOOL_SPEC 机检面（挂在 genesis 规格之后）════════
SPEC = r'''  davinci: { min: 2200, items: [
    { k: "一 · 采情：原话一字不改＋情境只记事实＋情源", re: "原话[：:]", ke: "Step one, the child's exact words and the situation", en: "([Ee]xact words|[Vv]erbatim|[Oo]riginal words)" },
    { k: "奇核：原话里那个不合常理的错位", re: "奇核[：:]", ke: "The oddness core", en: "([Oo]ddness core|[Ww]onder core|[Cc]ore oddity)" },
    { k: "S／D／E 三维与三方程", re: "(S=F|D=G|E=H)", n: 2, ke: "S, D, E and the three equations", en: "(S=F|D=G|E=H)" },
    { k: "角色卡（原创）", re: "角色卡", ke: "Original character cards", en: "[Cc]haracter" },
    { k: "分镜表（画面／台词／声音／情绪）", re: "分镜", ke: "Storyboard table", en: "[Ss]toryboard" },
    { k: "一个 html 围栏代码块：漫画示意稿", re: "```html", ke: "A fenced html block with the comic sketch" },
    { k: "图像提示词与视频镜头脚本", re: "(提示词|镜头)", n: 2, ke: "Image prompts and video shot script", en: "([Pp]rompt|[Ss]hot)" },
    { k: "五 · 回写：给孩子的三个问题＋空白格", re: "(回写|空白格)", n: 2, ke: "Write-back: three questions for the child and a blank panel", en: "([Ww]rite-back|[Bb]lank panel)" },
    { k: "〔交账〕行", re: "交账", ke: "The reckoning line", en: "([Rr]eckoning|[Tt]ally|[Aa]ccount line)" },
  ] },
'''
ANCH_SPEC = '''    { k: "〔交账〕行", re: "交账" , ke: "The reckoning line", en: "([Rr]eckoning|[Tt]ally|[Aa]ccount line)" },
  ] },
  /* iq 走的是 WDS_IQ_SYS 整段改道'''
w = sub1(w, ANCH_SPEC,
         ANCH_SPEC.replace("  /* iq 走的是 WDS_IQ_SYS 整段改道", SPEC + "  /* iq 走的是 WDS_IQ_SYS 整段改道"),
         "TOOL_SPEC.genesis 结尾")

# ════════ ④ 平台名录：模型自己得知道手上有这道 ════════
ANCH_CAT = '''交 5–8 条自带分岔与作废条件的候选分辨（只生不判，判交下一棒）"'''
w = sub1(w, ANCH_CAT,
         ANCH_CAT + '''
  + "\\n· **/达芬奇** 达芬奇发生体：家长或老师转述孩子一句由情激发的奇思妙想，交回原创艺术脚本（角色卡、分镜、四格漫画示意、给图像/视频模型的提示词），并留给孩子回写的格子——守住那一点「奇」，不讲道理"''',
         "平台名录 /发生场 那一行")

# ════════ ⑤ 前端：中英标签 ＋ 菜单 ════════
ZH = '''      tlGenesis: "发生场", tlGenesisS: "不答题，先布一场发生：摆料、上张力，交出五到八条自带分岔与作废条件的候选分辨",'''
f = sub1(f, ZH, ZH + '''
      tlDavinci: "达芬奇发生体", tlDavinciS: "孩子由情而生的奇思妙想 → SDE 补维守奇 → 原创艺术脚本、四格漫画示意稿、给图像/视频模型的提示词",''',
         "前端中文标签 tlGenesis")
EN = '''      tlGenesis: "Genesis field", tlGenesisS: "Stage a genesis instead of answering: lay out the stock, set up the clash, deliver 5-8 candidate distinctions each with its fork and kill condition",'''
f = sub1(f, EN, EN + '''
      tlDavinci: "Da Vinci Genesis", tlDavinciS: "A child's feeling-born wild idea → SDE fills the missing dimensions while keeping the oddness → an original art script, a four-panel comic sketch, and prompts for image/video models",''',
         "前端英文标签 tlGenesis")
MENU = '''    { k: "genesis", n: "tlGenesis", s: "tlGenesisS", cmd: ["发生场", "genesis", "布场"] }
  ];'''
f = sub1(f, MENU, '''    { k: "genesis", n: "tlGenesis", s: "tlGenesisS", cmd: ["发生场", "genesis", "布场"] },
    { k: "davinci", n: "tlDavinci", s: "tlDavinciS", cmd: ["达芬奇", "davinci", "发生体", "童画"] }
  ];''', "前端 TOOLS 末尾")

wr(W, w)
wr(F, f)
print("达芬奇发生体：后端四处、前端三处已落。接着跑 node tools/sim_chatsde_davinci.js")
