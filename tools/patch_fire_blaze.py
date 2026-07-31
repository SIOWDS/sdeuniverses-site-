#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把火从"一点余烬"改成熊熊大火

上一版的火只是一团模糊的橙色底光——远看只是个暖影子。真要烧起来，缺的是三样：
  ① **三层火舌**（外焰暗红 / 中焰橙 / 内焰黄白），三层各用不同的时长与相位，
     永远不同步——火之所以像火，全在于它从不重复自己；
  ② **形变**：底部定住（transform-origin:bottom），上部忽高忽低、左右微微摆（skewX），
     只改透明度是做不出火的；
  ③ **火星要多、要飞得高**，大小不一、横向有漂移。
体积也整体放大：图标那三团约两倍半，△ 那颗约两倍——原来太小，看着像没点着。
"""
FILES = {
    "portal": "/home/claude/site/public/assets/sde-portal.js",
    "modes": "/home/claude/site/public/assets/sde-modes.js",
    "wds": "/home/claude/site/public/wds-mode.js",
}


def sub1(txt, old, new, why):
    n = txt.count(old)
    assert n == 1, "锚点应恰好出现一次，实际 %d 次：%s（%s）" % (n, old[:60], why)
    return txt.replace(old, new, 1)


def tongues(pfx, kf):
    """三层火舌的公共样式。pfx=类名前缀，kf=keyframes 名。"""
    return (
        '".%s-fire b{position:absolute;left:50%%;bottom:0;transform-origin:50%% 100%%;'
        'border-radius:50%% 50%% 46%% 46%% / 68%% 68%% 32%% 32%%;'
        'animation-name:%s;animation-timing-function:ease-in-out;animation-iteration-count:infinite}" +\n'
        '    ".%s-fire .f1{width:96%%;height:88%%;filter:blur(9px);opacity:.55;'
        'background:radial-gradient(50%% 62%% at 50%% 100%%,#FF3D00 0%%,rgba(255,61,0,.5) 46%%,transparent 74%%);'
        'animation-duration:1.35s}" +\n'
        '    ".%s-fire .f2{width:66%%;height:70%%;filter:blur(5px);opacity:.8;'
        'background:radial-gradient(52%% 64%% at 50%% 100%%,#FF9A1F 0%%,rgba(255,140,20,.6) 48%%,transparent 76%%);'
        'animation-duration:1.02s;animation-delay:-.4s}" +\n'
        '    ".%s-fire .f3{width:38%%;height:48%%;filter:blur(2.6px);opacity:.92;'
        'background:radial-gradient(54%% 66%% at 50%% 100%%,#FFF3C4 0%%,#FFC93C 44%%,transparent 78%%);'
        'animation-duration:.78s;animation-delay:-.7s}" +\n'
        '    "@keyframes %s{0%%{transform:translateX(-50%%) scale(1,1) skewX(0deg)}'
        '22%%{transform:translateX(-50%%) scale(1.07,1.2) skewX(-4deg)}'
        '46%%{transform:translateX(-50%%) scale(.93,1.34) skewX(3deg)}'
        '68%%{transform:translateX(-50%%) scale(1.09,1.14) skewX(-2deg)}'
        '100%%{transform:translateX(-50%%) scale(1,1.04) skewX(1deg)}}" +'
    ) % (pfx, kf, pfx, pfx, pfx, kf)


# ── ① 入口页三个图标：熊熊 ──
s = open(FILES["portal"], encoding="utf-8").read()
i = s.index('    ".sdep-fire b{position:absolute;')
j = s.index('    ".sdep-sp{position:absolute;')
s = s[:i] + tongues("sdep", "sdepBurn").replace('    "@keyframes', '    "@keyframes') + "\n" + s[j:]
s = sub1(s, '".sdep-fire{position:absolute;left:50%;top:50%;width:132px;height:132px;',
         '".sdep-fire{position:absolute;left:50%;top:52%;width:190px;height:190px;', "火盘放大")
s = sub1(s, '".sdep-sp{position:absolute;bottom:16%;width:3px;height:3px;',
         '".sdep-sp{position:absolute;bottom:14%;width:3.5px;height:3.5px;', "火星变粗")
s = sub1(s, '100%{opacity:0;transform:translateY(-64px) scale(.15)}}',
         '100%{opacity:0;transform:translateY(-118px) scale(.12)}}', "火星飞得更高")
s = sub1(s, '      for (var s = 0; s < 9; s++) {', '      for (var s = 0; s < 18; s++) {', "火星加倍")
s = sub1(s, '        sp.style.left = (16 + s * 8.4) + "%";',
         '        sp.style.left = (10 + (s * 4.7) % 80) + "%";', "火星铺开")
s = sub1(s, '      fire.appendChild(document.createElement("b"));',
         '      ["f1", "f2", "f3"].forEach(function (fc) {\n'
         '        var t = document.createElement("b"); t.className = fc; fire.appendChild(t);\n'
         '      });', "三层火舌")
s = sub1(s, '.sdep-dotwrap{width:58px;height:58px}.sdep-fire{width:104px;height:104px}',
         '.sdep-dotwrap{width:58px;height:58px}.sdep-fire{width:146px;height:146px}', "窄屏也放大")
open(FILES["portal"], "w", encoding="utf-8").write(s)
print("入口页三团火：熊熊")

# ── ② 顶栏 △ ──
m = open(FILES["modes"], encoding="utf-8").read()
i = m.index('    ".sdemx-fire b{position:absolute;')
j = m.index('    ".sdemx-sp{position:absolute;')
m = m[:i] + tongues("sdemx", "sdemxBurn") + "\n" + m[j:]
m = sub1(m, '".sdemx-fire{position:absolute;left:50%;top:50%;width:46px;height:46px;',
         '".sdemx-fire{position:absolute;left:50%;top:54%;width:92px;height:92px;', "△ 火盘放大")
m = sub1(m, '100%{opacity:0;transform:translateY(-24px) scale(.15)}}',
         '100%{opacity:0;transform:translateY(-54px) scale(.12)}}', "△ 火星飞高")
m = sub1(m, '    for (var i2 = 0; i2 < 6; i2++) {', '    for (var i2 = 0; i2 < 12; i2++) {', "△ 火星加倍")
m = sub1(m, '      sp.style.left = (18 + i2 * 12) + "%";',
         '      sp.style.left = (12 + (i2 * 6.6) % 76) + "%";', "△ 火星铺开")
m = sub1(m, '    fire.appendChild(document.createElement("b"));',
         '    ["f1", "f2", "f3"].forEach(function (fc) {\n'
         '      var t = document.createElement("b"); t.className = fc; fire.appendChild(t);\n'
         '    });', "△ 三层火舌")
open(FILES["modes"], "w", encoding="utf-8").write(m)
print("顶栏 △：熊熊")

# ── ③ 侧栏 △ ──
w = open(FILES["wds"], encoding="utf-8").read()
i = w.index('    ".wdsm-pfire b{position:absolute;')
j = w.index('    ".wdsm-psp{position:absolute;')
w = w[:i] + tongues("wdsm-p", "wdsmBurn") + "\n" + w[j:]
w = sub1(w, '".wdsm-pfire{position:absolute;left:50%;top:50%;width:40px;height:40px;',
         '".wdsm-pfire{position:absolute;left:50%;top:54%;width:84px;height:84px;', "侧栏火盘放大")
w = sub1(w, '100%{opacity:0;transform:translateY(-22px) scale(.15)}}',
         '100%{opacity:0;transform:translateY(-50px) scale(.12)}}', "侧栏火星飞高")
w = sub1(w, '    for (var i = 0; i < 6; i++) {', '    for (var i = 0; i < 12; i++) {', "侧栏火星加倍")
w = sub1(w, '      sp.style.left = (18 + i * 12) + "%";',
         '      sp.style.left = (12 + (i * 6.6) % 76) + "%";', "侧栏火星铺开")
w = sub1(w, '    pf.appendChild(el("b"));',
         '    ["f1", "f2", "f3"].forEach(function (fc) { pf.appendChild(el("b", fc)); });', "侧栏三层火舌")
open(FILES["wds"], "w", encoding="utf-8").write(w)
print("侧栏 △：熊熊")
