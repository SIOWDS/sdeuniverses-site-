#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把「至少一个近邻来自领域之外」从**规范里的一句话**变成**能被检出的一道闸**。

这一条是 2026-07-29 全天审稿的扣分大头：几十篇里，跨域（E 维）是共同短板——
对手几乎全在本领域内部，而同一个机制往往在别的学科里已被人用别的名字研究了几十年。
可它此前只写在写作规范里，闸门只查"点名够不够三个 + 有没有判决性预测"，
三个对手全挤在同一学科里照样放行。

怎么让它可被机器检出——不靠猜，靠要求作者自己标：
  规范改为要求每个库外近邻**带一个固定格式的学科标注**「（学科：XXX）」，
  并在该节开头写一次「本文所属学科：XXX」。这样闸门只需解析标注，判据是确定的。
  这跟 NBR_CHECK_MARK 是同一个手法：想让什么被检查，就先让它有个可解析的形状。
兜底：标注缺失时退回关键词推断学科；推断不出就**不触发**——宁可漏查，不可乱判。
"""
import io, re, sys

P = "public/taste/idea-generator/index.html"
h = io.open(P, encoding="utf-8").read()
before = h

# ── ① 三处规范：把「三、」那条改成带可解析标注的版本 ──
OLD_A = """· 三、这三个近邻里，**至少一个必须来自问题所在领域之外的学科**。原因很实在：
  同一个机制常常在别的学科里已经被人用别的名字研究了几十年，而领域内的对手往往离得更远。
  只在本领域内找对手，是这类论文最常见也最致命的漏洞。"""
NEW_A = """· 三、这三个近邻里，**至少一个必须来自问题所在领域之外的学科**。原因很实在：
  同一个机制常常在别的学科里已经被人用别的名字研究了几十年，而领域内的对手往往离得更远。
  只在本领域内找对手，是这类论文最常见也最致命的漏洞。
  【格式硬要求 · NBR_DISC_MARK】这一节开头先写一行「本文所属学科：XXX」；
  随后每个库外近邻的出处后面，紧跟一个学科标注，格式就是「（学科：XXX）」——
  例如"（Bem, 1972，《自我知觉理论》）（学科：社会心理学）"。学科名写通行的学科名
  （社会学／心理学／人类学／经济学／管理学／法学／哲学／历史学／教育学／生理学／临床医学／
  组织行为学／科学社会学／语言学／政治学／计算机科学……），不要写成研究主题。
  这个标注不是排版要求，是给你自己的一道自查：三个标注若全和「本文所属学科」相同，
  说明你只在自家门内找了对手，请把其中至少一个换成真正跨学科的近邻。"""
OLD_B = """· 三、这三个里至少一个来自问题所在领域**之外**的学科。同一个机制常常在别的学科里已被人用别的名字研究了几十年，
  而领域内的对手往往离得更远——只在本领域找对手，是这类论文最常见也最致命的漏洞。"""
NEW_B = """· 三、这三个里至少一个来自问题所在领域**之外**的学科。同一个机制常常在别的学科里已被人用别的名字研究了几十年，
  而领域内的对手往往离得更远——只在本领域找对手，是这类论文最常见也最致命的漏洞。
  【格式硬要求 · NBR_DISC_MARK】本节开头写一行「本文所属学科：XXX」，每个库外近邻的出处后紧跟「（学科：XXX）」。
  三个标注若全与「本文所属学科」相同，说明你只在自家门内找了对手，至少换一个真正跨学科的近邻进来。"""

n = h.count(OLD_A)
assert n == 2, "预期两处一万字/两万字规范，实得 %d" % n
h = h.replace(OLD_A, NEW_A)
assert OLD_B in h, "提智规范那一条没找到"
h = h.replace(OLD_B, NEW_B, 1)
print("① 三处规范都加了可解析的学科标注要求（NBR_DISC_MARK）")

# ── ② 判据函数 ──
OLD_FN = "function nbrSectionOK(text){"
NEW_FN = r"""// ===== 跨学科闸 =====
// DISC_HINTS：标注缺失时的兜底推断表。故意只放**学科名**，不放研究主题词——
//   推断错一个学科，闸门就会冤枉一篇好论文，代价比漏查大。
const DISC_HINTS = ['社会学','心理学','社会心理学','认知心理学','发展心理学','人类学','民族学','经济学','行为经济学',
  '管理学','组织行为学','法学','法理学','哲学','伦理学','现象学','政治学','历史学','思想史','教育学','语言学',
  '传播学','新闻学','生理学','病理学','临床医学','流行病学','公共卫生','神经科学','生物学','生态学','营养学',
  '计算机科学','人工智能','统计学','数学','物理学','工程学','人因工程','科学社会学','知识社会学','宗教学','文学','美学','军事学'];
// nbrDiscTags：解析该节里的「本文所属学科：X」与各条「（学科：X）」。
function nbrDiscTags(seg){
  const s = String(seg||'');
  const own = (s.match(/本文所属学科\s*[：:]\s*([^\s，。；、（）()\n]{2,12})/) || [])[1] || '';
  const tags = (s.match(/[（(]\s*学科\s*[：:]\s*([^）)]{2,16})[）)]/g) || [])
    .map(x => (x.match(/学科\s*[：:]\s*([^）)]{2,16})/) || [])[1] || '')
    .map(x => x.trim()).filter(Boolean);
  return { own: own.trim(), tags: tags };
}
// nbrCrossOK：三个近邻是不是全挤在同一学科里。
//   返回 true=通过、false=没通过、null=看不出（缺标注又推断不出）——null 一律放行。
function nbrCrossOK(text){
  const t = String(text||'');
  const m = t.match(/(近邻检测|最近邻[^\n]{0,12}(切割|检测|对质)|近邻切割)[\s\S]{0,6000}/);
  if(!m) return null;                       // 连那一节都没有，交给 nbrSectionOK 去管
  const seg = m[0];
  const d = nbrDiscTags(seg);
  if(d.tags.length >= 2){
    const uniq = d.tags.filter((v,i)=>d.tags.indexOf(v)===i);
    if(uniq.length >= 2) return true;                       // 标注里就有两个以上不同学科
    if(d.own && uniq[0] && uniq[0] !== d.own) return true;   // 只有一个学科，但与本文学科不同
    return false;                                           // 三个标注同一个学科 → 只在门内找
  }
  // 兜底：没标注，看该节提到几个不同的学科名
  const found = DISC_HINTS.filter(x => seg.indexOf(x) >= 0);
  const uniq2 = found.filter((v,i)=>found.indexOf(v)===i);
  if(uniq2.length >= 2) return true;
  if(uniq2.length === 0) return null;       // 一个学科名都没提到 → 看不出，不冤枉
  return d.own ? (uniq2[0] !== d.own ? true : false) : null;
}
function nbrSectionOK(text){"""
assert OLD_FN in h
h = h.replace(OLD_FN, NEW_FN, 1)
print("② 加入 nbrDiscTags / nbrCrossOK（看不出就放行）")

# ── ③ 接进闸门 ──
OLD_G = """    const _needFix = paperText && (!nbrSectionOK(paperText) || _pn.missed.length > 0);
    if(_needFix){
      setStat(_pn.missed.length ? ('⚖ 新命名「'+_pn.name+'」还有 '+_pn.missed.length+' 篇站内近邻未交代，正在补写…')
                                : '⚖ 近邻检测未达标，正在补写这一节…');"""
NEW_G = """    // 第三关（跨学科）：三个近邻全挤在同一学科里 → 不过。看不出学科时返回 null，一律放行。
    const _cross = nbrCrossOK(paperText);
    const _needFix = paperText && (!nbrSectionOK(paperText) || _pn.missed.length > 0 || _cross === false);
    if(_needFix){
      setStat(_pn.missed.length ? ('⚖ 新命名「'+_pn.name+'」还有 '+_pn.missed.length+' 篇站内近邻未交代，正在补写…')
              : (_cross === false ? '⚖ 三个近邻全在同一学科内，正在换一个跨学科的对手补写…'
                                  : '⚖ 近邻检测未达标，正在补写这一节…'));"""
assert OLD_G in h
h = h.replace(OLD_G, NEW_G, 1)

OLD_C = """        NBR_FIX_INPUT(paperText, cfg.writeInput, (_pn.missed.length ? _pn.block : '')), fixSink, dummy, dummy, 4000);"""
NEW_C = """        NBR_FIX_INPUT(paperText, cfg.writeInput, (_pn.missed.length ? _pn.block : ''), _cross === false), fixSink, dummy, dummy, 4000);"""
assert OLD_C in h
h = h.replace(OLD_C, NEW_C, 1)

OLD_F = "function NBR_FIX_INPUT(paperText, writeInput, extraBlock){"
NEW_F = "function NBR_FIX_INPUT(paperText, writeInput, extraBlock, crossFailed){"
assert OLD_F in h
h = h.replace(OLD_F, NEW_F, 1)

OLD_F2 = """    + '· 这三个里至少一个来自问题所在领域**之外**的学科。\\n\\n'"""
NEW_F2 = """    + '· 这三个里至少一个来自问题所在领域**之外**的学科。\\n'
    + '· 本节开头写一行「本文所属学科：XXX」，每个库外近邻的出处后紧跟「（学科：XXX）」。\\n\\n'
    + (crossFailed ? '【本次特别注意】上一稿的三个近邻全落在同一个学科里——这正是这类论文最常见的漏洞。\\n请把其中至少一个换成真正来自别的学科的对手：同一个机制常常在别的学科里已被人用别的名字研究了几十年。\\n\\n' : '')"""
assert OLD_F2 in h, "补节指令里那一行没找到"
h = h.replace(OLD_F2, NEW_F2, 1)
print("③ 闸门接入第三关，补节指令带上换跨学科对手的要求")

if h == before:
    print("没有改动"); sys.exit(1)
io.open(P, "w", encoding="utf-8").write(h)
print("done")
