#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下拉菜单（成文 · PPT 那一张）必须能滚（2026-08-23 王德生报障：看不到最下面的）

病灶：`.wdsm-menu` 是 position:fixed、**没有 max-height 也没有 overflow**。
菜单从 4 档长到 17 档（＋导出／存到文件夹／成文历史三条），每条带副标约 50px ⇒ 整张 ~1000px。
顶栏按钮在 60px 处往下开，任何一块正常屏幕都装不下 ⇒ **末尾那几条点不到**，
而末尾正是今天刚加的应用文五档（通知／方案／总结／讲话／书信）与「成文历史」。

修法两件（缺一不可）：
① CSS：max-height ＋ overflow-y:auto ＋ **可见的细滚动条**（读者要看得出它能滚）；
   overscroll-behavior:contain 免得滚到底把底下的对话一起带着滚。
② JS：真正的可用高度只有开菜单那一刻才知道（按钮位置、窗口高度、是往下开还是往上开），
   所以 CSS 只兜底，落位后再按实际空间夹一次 —— 两处调用点共用同一个 menuFit。

幂等。
"""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(ROOT, 'public/wds-mode.js')
h = io.open(M, encoding='utf-8').read()
changed = []


def sub1(text, old, new, tag, done):
    if done in text:
        print('  · %s 已打过，跳过' % tag)
        return text
    n = text.count(old)
    assert n == 1, '锚点 %s 命中 %d 次' % (tag, n)
    changed.append(tag)
    return text.replace(old, new, 1)


# ── ① CSS ──────────────────────────────────────────────────────────────
old_css = ('    ".wdsm-menu{position:fixed;z-index:100002;background:var(--wpanel);'
           'border:1px solid var(--wline2);border-radius:12px;padding:6px;min-width:210px;'
           'box-shadow:0 10px 34px var(--wsh)}" +')
new_css = ('    /* max-height/overflow 是 2026-08-23 补的：菜单从 4 档长到 20 条，'
           '整张约 1000px，\n'
           '       而它从顶栏往下开——末尾几条（应用文五档、成文历史）在任何屏幕上都点不到。\n'
           '       ⚠ 滚动条**故意做成看得见的**：能滚而看不出能滚，等于没修。\n'
           '       精确高度由 menuFit() 在落位后按实际可用空间再夹一次，这里只兜底。 */\n'
           '    ".wdsm-menu{position:fixed;z-index:100002;background:var(--wpanel);'
           'border:1px solid var(--wline2);border-radius:12px;padding:6px;min-width:210px;'
           'box-shadow:0 10px 34px var(--wsh);max-height:calc(100vh - 96px);overflow-y:auto;'
           'overscroll-behavior:contain;-webkit-overflow-scrolling:touch;'
           'scrollbar-width:thin;scrollbar-color:var(--wline2) transparent}" +\n'
           '    ".wdsm-menu::-webkit-scrollbar{width:10px}" +\n'
           '    ".wdsm-menu::-webkit-scrollbar-track{background:transparent;margin:6px 0}" +\n'
           '    ".wdsm-menu::-webkit-scrollbar-thumb{background:var(--wline2);border-radius:6px;'
           'border:2px solid var(--wpanel)}" +\n'
           '    ".wdsm-menu::-webkit-scrollbar-thumb:hover{background:var(--wgold)}" +')
h = sub1(h, old_css, new_css, 'CSS 加滚动与可见滚动条', 'max-height:calc(100vh - 96px);overflow-y:auto')

# ── ② menuFit 助手（定义在两个调用点之前）────────────────────────────
old_anchor = '  try { layer.querySelector(".wdsm-pdfbtn").onclick = function () { exportPdf(); }; } catch (e) {}'
new_anchor = '''  /* 菜单落位后按**实际可用空间**夹一次高度。CSS 那条 calc(100vh - 96px) 只是兜底：
     真正能用的高度取决于按钮在哪、往下开还是往上开、这块屏有多高——只有开菜单那一刻知道。
     down=true ⇒ 从按钮下沿往下开，可用＝窗口高 − 按钮下沿 − 留白；
     down=false ⇒ 从按钮上沿往上开（menuAt 在按钮靠下时会这么做），可用＝按钮上沿 − 留白。
     ⚠ 下限 200px：宁可让它盖住一点，也不能夹成一条缝——那等于菜单没开。 */
  function menuFit(menu, rect, down) {
    try {
      var vh = window.innerHeight || 800;
      var room = down ? (vh - rect.bottom - 16) : (rect.top - 16);
      menu.style.maxHeight = Math.max(200, Math.round(room)) + "px";
    } catch (e) {}
  }
  try { layer.querySelector(".wdsm-pdfbtn").onclick = function () { exportPdf(); }; } catch (e) {}'''
h = sub1(h, old_anchor, new_anchor, 'menuFit 助手', 'function menuFit(menu, rect, down)')

# ── ③ 成文菜单调用 menuFit ────────────────────────────────────────────
old_pos = '''    var r = ev.currentTarget.getBoundingClientRect();
    menu.style.top = (r.bottom + 8) + "px";
    menu.style.left = Math.max(10, Math.min(r.left, window.innerWidth - menu.offsetWidth - 10)) + "px";'''
new_pos = '''    var r = ev.currentTarget.getBoundingClientRect();
    menu.style.top = (r.bottom + 8) + "px";
    menu.style.left = Math.max(10, Math.min(r.left, window.innerWidth - menu.offsetWidth - 10)) + "px";
    menuFit(menu, r, true);          // 17 档 ＋ 三条，不夹高度就看不到最下面那几条'''
h = sub1(h, old_pos, new_pos, '成文菜单夹高度', 'menuFit(menu, r, true);')

# ── ④ 通用 menuAt 也夹（顶栏与侧栏共用的那一份）──────────────────────
old_at = '''      if (r.top > 320) { menu.style.bottom = ((window.innerHeight || 800) - r.top + 8) + "px"; }
      else { menu.style.top = (r.bottom + 8) + "px"; }'''
new_at = '''      var _down = !(r.top > 320);
      if (!_down) { menu.style.bottom = ((window.innerHeight || 800) - r.top + 8) + "px"; }
      else { menu.style.top = (r.bottom + 8) + "px"; }
      menuFit(menu, r, _down);       // 往上开时可用高度是按钮上沿，不是窗口高'''
h = sub1(h, old_at, new_at, '通用菜单夹高度', 'menuFit(menu, r, _down);')

io.open(M, 'w', encoding='utf-8').write(h)
print('\n共改动 %d 处：' % len(changed))
for c in changed:
    print('  -', c)
