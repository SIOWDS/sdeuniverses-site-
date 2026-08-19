#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""入口页收火：三个图标恢复成克制的一团，熊熊大火只留在回入口的 △ 上

「熊熊大火」那句是对着顶栏那颗 △ 说的。入口页是三个入口并排的门面，
三团大火压过了三角形与「爱思乐园」，喧宾夺主——这里要的是"在烧"，不是"烧得旺"。

改法：入口页退回单层柔光 ＋ 九粒火星、火盘 132px；
      △ 那两处（顶栏 / 问WDS 侧栏）的三层火舌原样不动。
"""
P = "/home/claude/site/public/assets/sde-portal.js"
s = open(P, encoding="utf-8").read()


def sub1(old, new, why):
    global s
    n = s.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    s = s.replace(old, new, 1)


# 三层火舌 → 单层柔光
i = s.index('".sdep-fire b{position:absolute;')
j = s.index('".sdep-sp{position:absolute;')
s = s[:i] + (
    '".sdep-fire b{position:absolute;left:50%;bottom:8%;width:78%;height:62%;transform:translateX(-50%);'
    'border-radius:50%;'
    'background:radial-gradient(60% 80% at 30% 100%,rgba(255,110,0,.50),transparent 62%),'
    'radial-gradient(55% 80% at 62% 100%,rgba(255,190,60,.45),transparent 62%),'
    'radial-gradient(55% 80% at 86% 100%,rgba(255,70,0,.45),transparent 60%);'
    'filter:blur(7px);animation:sdepFlick 1.8s ease-in-out infinite}" +\n'
    '    "@keyframes sdepFlick{0%,100%{opacity:.7;transform:translateX(-50%) scaleY(1)}'
    '50%{opacity:1;transform:translateX(-50%) scaleY(1.14)}}" +\n'
) + s[j:]
sub1('".sdep-fire{position:absolute;left:50%;top:52%;width:190px;height:190px;',
     '".sdep-fire{position:absolute;left:50%;top:50%;width:132px;height:132px;', "火盘收回")
sub1('".sdep-sp{position:absolute;bottom:14%;width:3.5px;height:3.5px;',
     '".sdep-sp{position:absolute;bottom:16%;width:3px;height:3px;', "火星收细")
sub1('100%{opacity:0;transform:translateY(-118px) scale(.12)}}',
     '100%{opacity:0;transform:translateY(-64px) scale(.15)}}', "火星收低")
sub1('      for (var s = 0; s < 18; s++) {', '      for (var s = 0; s < 9; s++) {', "火星收回九粒")
sub1('        sp.style.left = (10 + (s * 4.7) % 80) + "%";',
     '        sp.style.left = (16 + s * 8.4) + "%";', "火星排布收回")
sub1('      ["f1", "f2", "f3"].forEach(function (fc) {\n'
     '        var t = document.createElement("b"); t.className = fc; fire.appendChild(t);\n'
     '      });',
     '      fire.appendChild(document.createElement("b"));', "单层火")
sub1('.sdep-dotwrap{width:58px;height:58px}.sdep-fire{width:146px;height:146px}',
     '.sdep-dotwrap{width:58px;height:58px}.sdep-fire{width:104px;height:104px}', "窄屏收回")
open(P, "w", encoding="utf-8").write(s)
print("入口页已收火（△ 那两处不动）")
