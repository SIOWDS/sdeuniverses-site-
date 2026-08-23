#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记分牌 · 客户端那一半（2026-08-23）

三件事：
  ① **剥**：交账那一行必须在入 history 之前从正文里拿掉——否则它会漏进对话历史、
     漏进将来的成文稿与导出 PDF。流式渲染那一路也要剥，不然读者会看着它一个字一个字冒出来。
  ② **核**：账上写的东西回正文里核一遍。只信它自己报的，就等于让它自己给自己发证书；
     「已有说法」与「外领域」必须在正文里真出现过，作废条件必须真是个条件句。
  ③ **摆**：四格记分牌挂在答案下面（家底／外领域／作废／新在），不合格的那格标出来。

⚠ 判定口径两条，别改松：
  · 「新在：无（只到复述）」**不算失败**，算如实申报，显示成中性——这条出路是上一刀特意留的，
    界面上把它标红，等于逼基底下次编一个。
  · 核不上正文的那一项，一律按**未做**算，不按它自报的算。
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


# ── ① 解析 / 核对 / 渲染 三个函数（挂在 renderFollows 之前）──────────
FUNCS = r'''  /* ════════ 记分牌：把「这一答到底走没走那几步」变成可数的 ════════
     服务端要求每一答末尾交一行 `〔交账〕已有说法：… ｜ 外领域：… ｜ 作废条件：… ｜ 新在：…`。
     这里做三件事：把那一行从正文里**剥掉**（它不该进历史、成文稿与 PDF）、
     回正文**核对**（只信它自报等于让它自己发证书）、**摆成四格**给读者看。 */
  var LEDGER_RE = /\n*[〔【\[]\s*交账\s*[〕】\]][^\n]*/;
  function ledgerStrip(text) { return String(text || "").replace(LEDGER_RE, "").replace(/\s+$/, ""); }
  function ledgerField(line, name) {
    // 字段之间用全角或半角竖线分隔；末字段吃到行尾。冒号全角半角都认。
    var re = new RegExp(name + "\\s*[：:]\\s*([^｜|]*)");
    var m = line.match(re);
    return m ? String(m[1]).replace(/\s+$/, "").replace(/^\s+/, "") : "";
  }
  function ledgerEmpty(v) { return !v || /^(无|none|-|—|不适用)/i.test(v); }
  /* take：从整段答案里取出账并剥净。回 null ＝ 这一答没交账（分身档不装这条规格，属正常）。 */
  function ledgerTake(text) {
    var s = String(text || "");
    var m = s.match(LEDGER_RE);
    if (!m) return null;
    var line = m[0].replace(/^\s+/, "");
    var body = ledgerStrip(s);
    var stockRaw = ledgerField(line, "已有说法");
    var stock = ledgerEmpty(stockRaw) ? [] : stockRaw.split(/[；;、]/).map(function (x) { return x.trim(); }).filter(Boolean);
    return {
      body: body, line: line,
      stock: stock,
      field: ledgerField(line, "外领域"),
      falsify: ledgerField(line, "作废条件"),
      newness: ledgerField(line, "新在"),
    };
  }
  /* 核对：账上的东西回正文里找。找不到一律按**未做**算，不按它自报的算。 */
  function ledgerAudit(led, body) {
    var b = String(body || "");
    var seen = (led.stock || []).filter(function (x) {
      var k = x.replace(/[的了在是（）()《》"'「」]/g, "").slice(0, 6);
      return k.length >= 2 && b.indexOf(k) >= 0;
    });
    var fieldOk = !ledgerEmpty(led.field) && b.indexOf(String(led.field).slice(0, 4)) >= 0;
    // 作废条件必须真是个条件句：有条件词，且有「作废/推翻/不成立」这一类结果词。
    var fal = String(led.falsify || "");
    var falOk = !ledgerEmpty(fal) && /若|如果|一旦|当/.test(fal) && /作废|推翻|不成立|失效|就错/.test(fal);
    var told = !ledgerEmpty(led.newness);          // 如实写「无」不算失败，算申报
    return {
      stockN: seen.length, stockClaim: (led.stock || []).length,
      stockOk: seen.length >= 2,
      fieldOk: fieldOk, falOk: falOk, newOk: told,
      newTold: !told,                              // 明说「只到复述」——中性，不标红
    };
  }
  function ledgerRender(cell, led, body) {
    if (!led || cell.ledger) return;
    var a = ledgerAudit(led, body);
    var box = el("div", "wdsm-led");
    box.appendChild(el("i", "lh", t("ledH")));
    function chip(okv, label, tip, neutral) {
      var c = el("i", "lc" + (neutral ? " nu" : (okv ? " ok" : " no")), label);
      c.title = tip;
      box.appendChild(c);
    }
    chip(a.stockOk, t("ledStock") + " " + a.stockN + (a.stockClaim > a.stockN ? ("/" + a.stockClaim) : ""),
      (led.stock || []).join("；") + (a.stockClaim > a.stockN ? "\n（其中 " + (a.stockClaim - a.stockN) + " 个在正文里找不到，按未做算）" : ""));
    chip(a.fieldOk, t("ledField") + (a.fieldOk ? " ✓" : " —"),
      led.field || "（没有别的领域进来顶）");
    chip(a.falOk, t("ledFal") + (a.falOk ? " ✓" : " —"),
      led.falsify || "（没给出作废条件）");
    chip(a.newOk, t("ledNew") + (a.newOk ? " ✓" : " —"),
      led.newness || "（没写）", a.newTold);
    cell.turn.appendChild(box); cell.ledger = box; cell.ledgerAudit = a;
  }

'''
h = sub1(h, '  function renderFollows(cell, qs) {', FUNCS + '  function renderFollows(cell, qs) {',
         '记分牌三函数', 'function ledgerTake(text)')

# ── ② finish() 里：先剥再入历史，再摆记分牌 ────────────────────────
old_fin = '''          if (answer) {
            cell.a.innerHTML = mdRender(answer);'''
new_fin = '''          if (answer) {
            /* 交账那一行必须在这里剥掉：再往下就进 history、进成文稿、进导出 PDF 了。 */
            var _led = ledgerTake(answer);
            if (_led) answer = _led.body;
            cell.a.innerHTML = mdRender(answer);'''
h = sub1(h, old_fin, new_fin, 'finish 剥账', 'var _led = ledgerTake(answer);')

old_hist = '            history.push({ role: "wds", text: answer }); stSave(history); mountActs(cell, answer);'
new_hist = ('            history.push({ role: "wds", text: answer }); stSave(history); mountActs(cell, answer);\n'
            '            if (_led) ledgerRender(cell, _led, answer);      // 记分牌挂在正文之外，不进导出稿')
h = sub1(h, old_hist, new_hist, 'finish 摆记分牌', 'ledgerRender(cell, _led, answer)')

# ── ③ 流式渲染也剥（否则读者会看着它一个字一个字冒出来）──────────
old_stream = '      cell.a.innerHTML = mdRender(answer) + "<span class=\'cur\'>▊</span>";'
new_stream = '      cell.a.innerHTML = mdRender(ledgerStrip(answer)) + "<span class=\'cur\'>▊</span>";'
h = sub1(h, old_stream, new_stream, '流式渲染剥账', 'mdRender(ledgerStrip(answer))')

# ── ④ 文案（中英）与样式 ──────────────────────────────────────────
old_zh = '      srcSite: "站内文献", srcWeb: "站外来源 · 联网搜索", followsH: "接着可以问",'
new_zh = ('      srcSite: "站内文献", srcWeb: "站外来源 · 联网搜索", followsH: "接着可以问",\n'
          '      ledH: "这一答走了几步", ledStock: "家底", ledField: "外领域", ledFal: "作废条件", ledNew: "新在",')
h = sub1(h, old_zh, new_zh, '中文文案', 'ledH: "这一答走了几步"')

old_en = '    srcSite: "ON-SITE SOURCES", srcWeb: "WEB SOURCES", followsH: "ASK NEXT",'
new_en = ('    srcSite: "ON-SITE SOURCES", srcWeb: "WEB SOURCES", followsH: "ASK NEXT",\n'
          '    ledH: "STEPS TAKEN", ledStock: "prior views", ledField: "other field", ledFal: "falsifier", ledNew: "what\'s new",')
h = sub1(h, old_en, new_en, '英文文案', 'ledH: "STEPS TAKEN"')

old_css = '    ".wdsm-follows{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}" +'
new_css = ('    ".wdsm-led{margin-top:12px;display:flex;flex-wrap:wrap;align-items:center;gap:6px}" +\n'
           '    ".wdsm-led .lh{font-style:normal;font-size:10.5px;letter-spacing:1px;color:var(--wdim2);margin-right:4px}" +\n'
           '    ".wdsm-led .lc{font-style:normal;font-size:11px;border-radius:999px;padding:3px 9px;border:1px solid var(--wline);'
           'color:var(--wdim);background:var(--wfill2);cursor:help}" +\n'
           '    ".wdsm-led .lc.ok{color:var(--wgold2);border-color:var(--wline2)}" +\n'
           '    ".wdsm-led .lc.no{color:#8B7A6A;border-style:dashed}" +\n'
           '    ".wdsm-led .lc.nu{color:var(--wdim2)}" +\n'
           '    ".wdsm-follows{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}" +')
h = sub1(h, old_css, new_css, '记分牌样式', '".wdsm-led{margin-top:12px')

io.open(M, 'w', encoding='utf-8').write(h)
print('\n共改动 %d 处：' % len(changed))
for c in changed:
    print('  -', c)
