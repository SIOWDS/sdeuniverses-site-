#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记分牌 · 服务端那一半：每一答末尾交一行账（2026-08-23）

前三刀（使命／清家底／朝五维）都只写在提示词里 —— **它是不是真走了，谁也不知道**。
不测量就等于没做：很可能每样只给一句敷衍，而屏幕上看不出任何差别。

做法刻意选了「同一次调用里多写一行」，不是再花一次调用去评：
  · 零成本（几十个 token），每轮都跑得起；
  · 交的是**事实清点**（摆了哪几个已有说法、哪个外领域真进来顶过、作废条件是哪句、新在哪），
    **不是分数** —— 自评分数必然通胀，那条铁律前一刀已经写死了，这里同样禁。
  · 判定合格与否由**客户端机检**做（还要回正文里核对，防交空账），基底只负责如实报。

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


LEDGER = r'''/* ═══ 交账（2026-08-23）═══════════════════════════════════════════
   前三刀只写在提示词里，走没走过没人知道。这一行把它变成可数的。
   ⚠ 三条设计约束，改之前先读：
     ① 交的是**清点**不是分数（自评必通胀，前一刀已禁，这里再禁一次）；
     ② 必须是**固定格式的一行**——客户端要把它剥下来做成记分牌，
        剥不干净就会漏进正文与将来的成文稿里；
     ③ 账上写的东西**正文里必须出现过**，客户端会回正文核对，交空账当场看得出来。 */
const SDE_METHOD_LEDGER = "\n\n【最后一行 · 交账（格式固定，一行写完；不要标题、不要分点、不要代码块）】"
  + "正文写完后另起一行，原样按下面这个格式交一行账。**这一行会被界面剥下来做成记分牌，不进正文、也不进将来的成文稿**，"
  + "所以它不必好看，只要准："
  + "\n〔交账〕已有说法：甲的说法；乙的说法 ｜ 外领域：某某领域 ｜ 作废条件：若观察到 X，本判断作废 ｜ 新在：一句话"
  + "\n· **已有说法至少两个**，写你清家底那一步真摆出来的那几个；**正文里也必须出现过**，不许只写在这一行上。"
  + "\n· **外领域**写正文里真进来顶过的那一个（删掉它论证会塌的那个）；没有就写「无」。"
  + "\n· **作废条件**照抄正文里那一句；给不出就写「无」。"
  + "\n· **新在**写你结算出的那一条；这一答只到复述就写「无（只到复述）」——**如实写「无」不丢人，编一个才丢人**。"
  + "\n· **不许在这一行里给自己打分**，也不许写「本答创新度较高」这类评语：这是清点，不是评价。";
'''

old_anchor = 'const SDE_METHOD_SETTLE = '
h = sub1(h, old_anchor, LEDGER + old_anchor, 'SDE_METHOD_LEDGER 常量', 'const SDE_METHOD_LEDGER')

# 两档都装：结算之后（交账是收尾动作，必须排在最后）
h = sub1(h,
         '  + SDE_METHOD_FIVE\n  + SDE_METHOD_SETTLE\n  + "\\n输出要求',
         '  + SDE_METHOD_FIVE\n  + SDE_METHOD_SETTLE\n  + SDE_METHOD_LEDGER\n  + "\\n输出要求',
         '深度档接入交账', 'SDE_METHOD_SETTLE\n  + SDE_METHOD_LEDGER\n  + "\\n输出要求')

h = sub1(h,
         '  + SDE_METHOD_FIVE\n  + SDE_METHOD_SETTLE;',
         '  + SDE_METHOD_FIVE\n  + SDE_METHOD_SETTLE\n  + SDE_METHOD_LEDGER;',
         '标准档接入交账', 'SDE_METHOD_SETTLE\n  + SDE_METHOD_LEDGER;')

io.open(W, 'w', encoding='utf-8').write(h)
print('\n共改动 %d 处：' % len(changed))
for c in changed:
    print('  -', c)
