#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""成文前先做一次占位者实搜（2026-08-23）

缘起是一份真产出的实测：《从信息搬运到发生识别》（29,740 字，盲评 122.65）——
四刀之后 S/D/F 都抬起来了，**I=110、E=108 仍然塌着**，而原因非常具体：
它盘的八位「最近邻」全是 1977–2014 的老经典，真正的正主（TEQSA/Lodge/Dawson 2023–2026 那一整片、
Geels 的 niche–regime、Luhmann 的码本）**一位都没碰**。
⇒ 基底的库存对最近三年最薄，而这类题恰恰是最近三年的题。**I/E 的天花板要靠联网。**

这一刀只加一次调用（nbrChain 的四趟并发搜索，与评分那一路复用同一条专用链），
只加在**真需要盘最近邻的档**上：提炼成文／论文（两档）／提纲／公众号。
报告、诗歌、通知、函件这些不加——那些档盘最近邻是噪声。

顺带钉两条纪律，都是从同一份稿子里抠出来的真缺陷：
  · **网址只准照抄**——那篇的参考文献里把王德生两条挂在 `https://wds.com/...`，站点根本不存在；
  · **不许声称一份没写出来的清单**——那篇写「共纳入 22 件／17 件／11 件，与正文逐件对应」，全文没有这份清单。

幂等。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'src/worker.js')
h = io.open(W, encoding='utf-8').read()
changed = []


def sub1(text, old, new, tag, done):
    if done in text:
        print('  · %s 已打过，跳过' % tag)
        return text
    n = text.count(old)
    assert n == 1, '锚点 %s 命中 %d 次' % (tag, n)
    changed.append(tag)
    return text.replace(old, new, 1)


# ── ① 成文侧的用法块（挂在 nbrChainBlock 之后，只补成文特有的三条）────────
USAGE = r'''/* 成文那一路怎么用这份名单（2026-08-23）。nbrChainBlock 已经写了四条通用纪律，
   这里只补成文特有的三条，每一条都是从一份真产出的实测缺陷里抠出来的：
     · 只盘老经典＝没做敌意拓宽（那篇八位最近邻全在 1977–2014，正主在 2023–2026）；
     · 编造网址（把两篇挂在一个不存在的站点上）；
     · 声称一份没有写出来的材料清单（「共纳入 22 件…与正文逐件对应」，全文找不到那份清单）。 */
function distNbrUsage(hasList) {
  return "\n\n【成文时怎么用这份名单（三条硬的）】"
    + (hasList
        ? "\n① **最近邻盘点里至少三位要出自上面这份名单**。只盘二三十年前的经典而不碰近三年真正在做同一件事的人，"
          + "等于没做敌意拓宽——**近三年正是你自己记忆最薄的那一段，名单是来补这一段的**。"
        : "\n① 这一趟一条都没召回：最近邻盘点**按〔未核验〕写**，并在正文里如实说明这一节没有经过站外检索。"
          + "**不许拿记忆里的老经典充数，更不许说「据我所知尚无人提出」。**")
    + "\n② **参考文献与正文里的每一个网址，只准从上面这份名单或站内资料里照抄**，一个字符都不许自己拼。"
      + "记得住篇名记不住网址，就只写篇名——**编一个能打开的样子出来，是这一篇里最严重的一种错**。"
    + "\n③ 凡写「共纳入 N 件材料」「上述清单与正文逐件对应」这类**可被核对的话**，要么把那份清单真的写出来，"
      + "要么这句话根本不要写。**一句可核验而为假的话，比论证薄弱伤得更重。**";
}
'''
h = sub1(h, '\n// 把搜索结果码成给基底看的块。编号 [W1..] 与前端',
         '\n' + USAGE + '\n// 把搜索结果码成给基底看的块。编号 [W1..] 与前端',
         'distNbrUsage 常量', 'function distNbrUsage(hasList)')

# ── ② distill 里：按档取一次占位者实搜（惰性、只跑一次）──────────────────
old_convo = '''      const convoCut = convoFull.length - convo.length;'''
new_convo = '''      const convoCut = convoFull.length - convo.length;
      /* 【成文前的占位者实搜】只加在真要盘最近邻的档上；报告/诗歌/应用文不加（那里盘最近邻是噪声）。
         走的是评分那一路已有的专用链 nbrChain（四趟并发：同向占位／对立者／外圈学科／方法学），
         不另造一套。惰性 + 只跑一次：提纲那一趟与正文各趟共用同一份结果。 */
      const DIST_NBR_KINDS = { essay: 1, paper: 1, paper1: 1, outline: 1, wechat: 1 };
      let _distNbrP = null;
      const distNbrGet = () => {
        if (_distNbrP) return _distNbrP;
        if (!DIST_NBR_KINDS[kind]) { _distNbrP = Promise.resolve(null); return _distNbrP; }
        /* 种子取**读者自己的第一问**（这一场的原初问题），不取工序标题也不取整篇——
           把一整场塞进 34 字的查询里等于随机截一段（评分那一路踩过这个坑）。 */
        const _t0 = (turns.find((t) => t && t.role !== "wds" && String(t.text || "").trim()) || {});
        const _seed = String(_t0.text || b.title || "").trim();
        if (!_seed) { _distNbrP = Promise.resolve(null); return _distNbrP; }
        _distNbrP = nbrChain(env, _seed, (rvendor === "glm" ? KEY : ""), convo.slice(0, 20000))
          .catch(() => null);
        return _distNbrP;
      };
      /* 块 + 状态一起回：状态要发给读者看（失败必须可见——静默失败等于把没做的检测记成做过了）。 */
      const distNbrBlock = (nc) => {
        if (!nc) return "";
        return "\\n\\n" + (nc.items.length ? nbrChainBlock(nc) : "【站外占位者检索 · 这一趟一条也没召回】")
          + distNbrUsage(!!nc.items.length);
      };'''
h = sub1(h, old_convo, new_convo, 'distill 取占位者', 'const distNbrGet = () =>')

# ── ③ 拆趟路：注入 BASE（提纲与各节共用）────────────────────────────────
# 两处锚点逐字相同，只有缩进不同（拆趟路 16 空格 / 一趟路 14 空格）——按缩进区分。
old_base = '''\n                + (prof && prof.term ? prof.term : "");   // 术语闸必须留在最末'''
new_base = '''\n                + (prof && prof.term ? prof.term : "");   // 术语闸必须留在最末
              /* 占位者名单**排在术语闸之后**是刻意的：它是材料不是人格，压不到闸上；
                 而它必须进 BASE —— 提纲那一趟就要靠它决定「最近邻盘点」那一节写谁。 */
              const _nbrDist = await distNbrGet();
              const NBRB = distNbrBlock(_nbrDist);
              if (_nbrDist) {
                if (_nbrDist.items.length) controller.enqueue(_sseBytes({ t: "web", v: _nbrDist.items }));
                controller.enqueue(_sseBytes({ t: "note", v: _nbrDist.items.length
                  ? ("已先做一次站外占位者检索：召回 " + _nbrDist.items.length + " 条"
                     + (_nbrDist.ok ? "（覆盖够）" : "（覆盖不足：" + _nbrDist.reason + "，最近邻那一节会按〔未核验〕写）"))
                  : "站外占位者检索这一趟一条也没召回（多半是没有可用的搜索 Key）：最近邻那一节会按〔未核验〕写。" }));
              }'''
h = sub1(h, old_base, new_base, '拆趟路注入', 'const _nbrDist = await distNbrGet();')

# ── ④ 一趟出全篇那一路：注入 sys ────────────────────────────────────────
old_one = '''\n              + (prof && prof.term ? prof.term : "");   // 术语闸必须留在最末'''
new_one = '''\n              + (prof && prof.term ? prof.term : "")   // 术语闸必须留在最末
              + await (async () => {
                  const nc = await distNbrGet();
                  if (nc) {
                    if (nc.items.length) controller.enqueue(_sseBytes({ t: "web", v: nc.items }));
                    controller.enqueue(_sseBytes({ t: "note", v: nc.items.length
                      ? ("已先做一次站外占位者检索：召回 " + nc.items.length + " 条"
                         + (nc.ok ? "（覆盖够）" : "（覆盖不足：" + nc.reason + "）"))
                      : "站外占位者检索这一趟一条也没召回：最近邻那一节会按〔未核验〕写。" }));
                  }
                  return distNbrBlock(nc);
                })();'''
h = sub1(h, old_one, new_one, '一趟路注入', 'const nc = await distNbrGet();')

# ── ⑤ 拆趟路：把名单真的接到 psys 与 ssys 上（BASE 只是算了，没接等于白搜）──
h = sub1(h, '                const psys = BASE + "\\n\\n【本次任务】只出一份提纲，不写正文。\\n" + SPEC.spec + writerBlock(styleId)',
         '                const psys = BASE + NBRB + "\\n\\n【本次任务】只出一份提纲，不写正文。\\n" + SPEC.spec + writerBlock(styleId)',
         '提纲趟接名单', 'const psys = BASE + NBRB')
h = sub1(h, '              const ssys = BASE + writerBlock(styleId)   // 分节各趟也要带风格，否则前后两节像两个人写的',
         '              const ssys = BASE + NBRB + writerBlock(styleId)   // 分节各趟也要带风格，否则前后两节像两个人写的',
         '正文各趟接名单', 'const ssys = BASE + NBRB')

io.open(W, 'w', encoding='utf-8').write(h)
print('\n共改动 %d 处：' % len(changed))
for c in changed:
    print('  -', c)
