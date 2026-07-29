# -*- coding: utf-8 -*-
"""把 SDE 经济学频道挂进 /business/ 栏目页：顶栏子导航 + 频道区块 + 徽标计数。"""
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "public" / "business" / "index.html"
h = P.read_text(encoding="utf-8")
assert "/business/sde-economics/" not in h, "已挂载过，勿重复运行"

# ① 子导航配色（紧跟学员频道那条规则）
css_old = '.nav-bar-sub a[href="/business/from-students/"]{color:#A0651F}'
css_new = (css_old + '\n.nav-bar-sub a[href="/business/sde-economics/"]{color:#9A2B26}')
assert css_old in h and css_new not in h
h = h.replace(css_old, css_new, 1)

# ② 顶栏子导航条：把频道排在最前
nav_old = ('    <a href="#biz-power" class="zh-only">权力发生学</a>'
           '<a href="#biz-power" class="en-only">Power</a>')
nav_new = ('    <a href="/business/sde-economics/" class="zh-only">SDE经济学频道</a>'
           '<a href="/business/sde-economics/" class="en-only">SDE Economics</a>\n' + nav_old)
assert nav_old in h
h = h.replace(nav_old, nav_new, 1)

# ③ 徽标：加频道计数
bd_old = ('<span class="zh-only">＋学员频道 50 篇 · 长文合辑 · 6 篇 / 2 板块 · 持续增补</span>'
          '<span class="en-only">Essay Collection · 6 pieces / 2 blocks</span>')
bd_new = ('<span class="zh-only">＋SDE经济学频道 2 篇 · ＋学员频道 50 篇 · 长文合辑 · 6 篇 / 2 板块 · 持续增补</span>'
          '<span class="en-only">＋SDE Economics Channel · Essay Collection · 6 pieces / 2 blocks</span>')
assert bd_old in h
h = h.replace(bd_old, bd_new, 1)

# ④ 频道区块，插在「商业：发现还是发生？」长论块之后、权力发生学之前
anchor = '    <div class="block" id="biz-power">'
block = '''    <div class="block" id="biz-sde-econ" style="margin-bottom:2.6rem">
      <div class="block-head">
        <span class="block-num" style="color:#9A2B26">◆</span>
        <span class="block-title"><span class="zh-only">频道 · SDE 经济学</span><span class="en-only">Channel · SDE Economics</span></span>
      </div>
      <p class="block-desc zh-only">经济学有两套成熟的账：一套记产出，一套记代价。本频道加的是第三套——记路径。一个经济体这十年选择用什么技术、按什么规则去形成新结构，这个「下一步往哪走」的选择规则不是存量也不是流量，因此任何资产负债表都装不下它。<b>装不下的代价是具体的。</b></p>
      <p class="block-desc en-only">Economics keeps two mature ledgers: one for output, one for cost. This channel adds a third — for the path itself, which is neither a stock nor a flow, and therefore fits on no balance sheet.</p>
      <div class="art-grid">
        <a class="art feature" href="/business/sde-economics/" style="display:block;border-left-color:#9A2B26">
          <span class="k" style="color:#9A2B26"><span class="zh-only">SDE 经济学频道 · 开栏 2 篇 · 约 4.1 万字 · 30 页 · 持续增补</span><span class="en-only">SDE ECONOMICS CHANNEL · 2 PIECES · ~41k CHARS</span></span>
          <h4><span class="zh-only">代偿增长：一种所有账本都读数正常的增长</span><span class="en-only">Compensatory Growth: The Kind Every Ledger Calls Healthy</span></h4>
          <p class="zh-only">有一种增长，损耗被完整识别、被计量、被公开报告，修复预算逐年上升并接受审计，受损方获得补偿——所有环节都在运转，唯独没有任何一个环节的职责，是追问这条路径本身是否应当继续。它在现行的每一本账上都及格。开栏两篇：一篇是完整的研究纲领（三方程 · 二重回写 · 发生土壤账户 · 有效生成能力的显式构造 · 七项可证伪假设），一篇是写给所有人的通俗解剖（从心脏的代偿期，到一家公司、一个人、一个行业）。</p>
          <p class="en-only">A growth regime in which losses are measured, repair budgets rise yearly and are audited, and the injured are compensated — every part working, except that no part is charged with asking whether the path itself should continue. Two opening pieces: a full research programme, and a plain-language anatomy.</p>
          <span class="rd" style="color:#9A2B26"><span class="zh-only">进入频道 →</span><span class="en-only">Enter the channel →</span></span>
        </a>
      </div>
    </div>

'''
assert anchor in h and 'id="biz-sde-econ"' not in h
h = h.replace(anchor, block + anchor, 1)

# ⑤ 结构自检
for t in ("div", "span", "a", "p", "section", "main", "nav", "header", "footer", "style", "body", "html"):
    o, c = h.count(f"<{t} ") + h.count(f"<{t}>"), h.count(f"</{t}>")
    assert o == c, f"<{t}> 不配对 {o}/{c}"
P.write_text(h, encoding="utf-8")
print("商业栏目页已挂载频道：子导航 + 区块 + 徽标 ·", len(h), "字节")
