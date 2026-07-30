#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sim 第三刀：覆盖模式 D（站外自动检索）与成品体例开关（散文体/论文体）。

用法：python3 tools/patch_sim_forge_mode_d.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(ROOT, "tools", "sim_paradigm_forge.js")


def sub1(h, old, new, name):
    assert old in h, "锚不到：" + name
    assert h.count(old) == 1, "锚不唯一（%d）：%s" % (h.count(old), name)
    return h.replace(old, new, 1)


SECTION = r"""
  /* ============ 二十七、模式 D（站外三领域·联网检索）与成品体例 ============
     这一路的要害不是"能不能搜到"，而是**搜不到时会不会假装搜过**。
     所以四条失败路径（没检索 Key／搜得太少／基底给不出成形的源／链接没拿到）
     都要如实说出来并指路 F 模式，一条都不许静默降级。 */

  await step('二十七、模式 D：拆检索词 → 三轮检索 → 挑三家斜对立的', async () => {
    const c = await boot();
    pickModeD(c);
    const done = await runPipeline(c, 35000);
    ok('跑到底', done, c.$('stat-review').textContent);
    const q = c.calls.filter(x => /把它拆成\*\*三个检索词\*\*/.test(x.user)).pop();
    ok('先拆检索词', !!q);
    ok('要求落在三个不同学科上', q && /三个不同的学科/.test(q.user));
    ok('检索词限长（超长召回反而差）', q && /≤ 12 个字/.test(q.user));
    ok('拆词也带斜对立的判据', q && /斜/.test(q.user));
    ok('三轮检索都打了 /api/wds/websearch', (c.webQ || []).length === 3, JSON.stringify(c.webQ));
    const pk = c.calls.filter(x => /请从里面挑出\*\*三家现行理论\*\*/.test(x.user)).pop();
    ok('把检索结果交给基底去挑', pk && /\[W1-1\]/.test(pk.user));
    ok('挑三家时也给斜对立的判据', pk && /斜着的对立|斜对立|斜着/.test(pk.user));
    ok('一个字都不许编（作者/年份/链接只许照抄）', pk && /一个字都不许编/.test(pk.user));
    ok('宁可少挑一家也不许造假出处', pk && /不许造一个像真的出处/.test(pk.user));
    ok('三家已就位', /三家已就位/.test(c.$('srcState').textContent), c.$('srcState').textContent);
    ok('红字提醒站外来源要自己核对链接', /点开每个链接核对/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('横幅标出站外来源', /联网找/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
  });

  await step('二十七之二、模式 D 自动切到论文体，且成品照论文骨架写', async () => {
    const c = await boot();
    pickModeD(c);
    ok('选了 D 就默认论文体', c.$('genreSel').value === 'paper', c.$('genreSel').value);
    ok('提示说清论文体要给链接', /三家出处必须给可点开核对的链接/.test(c.$('genreNote').textContent));
    await runPipeline(c, 35000);
    const ol = c.calls.filter(x => /列一份学术论文的节次目录/.test(x.user)).pop();
    ok('目录换成论文骨架', ol && /文献综述/.test(ol.user) && /参考文献/.test(ol.user));
    ok('论文体也禁"研究方法"这类节次（工序不进成品）', ol && /不许出现.*研究方法/.test(ol.user));
    const wr = c.calls.filter(x => /照下面的目录，把整篇文章/.test(x.user)).pop();
    ok('成文 system 是论文体', wr && /跨学科的学术创新论文/.test(wr.system));
    ok('论文体正面写三家（文献综述不是车间痕迹）', wr && /三家理论要正面写出来/.test(wr.system));
    ok('论文体照样禁工艺词', wr && /不许出现碰撞、对撞/.test(wr.system));
    ok('论文体照样禁学派专名', wr && /不许出现学派专名/.test(wr.system));
    ok('把三家出处交给写手了', wr && /三家的出处/.test(wr.user));
    ok('链接只许照抄不许编', wr && /链接只许照抄、不许编/.test(wr.user));
  });

  await step('二十七之三、散文体是站内碰撞的默认，改过之后不被模式覆盖', async () => {
    const c = await boot();
    ok('模式 A 默认散文体', c.$('genreSel').value === 'essay', c.$('genreSel').value);
    // 用户手动改成论文体后，再切模式不许把他的选择改回去
    c.$('genreSel').value = 'paper';
    c.$('genreSel').dispatchEvent(new c.win.Event('change', { bubbles: true }));
    c.click('.mode[data-mode="C"]');
    ok('用户改过之后以用户为准', c.$('genreSel').value === 'paper', c.$('genreSel').value);
    c.click('.mode[data-mode="A"]');
    ok('切回站内模式也不擅自改回', c.$('genreSel').value === 'paper', c.$('genreSel').value);
  });

  await step('二十七之四、去痕迹词表分层：论文体放行"三家"，工艺词恒查', async () => {
    const c = await boot();
    const t = '本文综合三家理论，这三篇文章的矛盾轴由碰撞撞出。';
    c.$('genreSel').value = 'essay';
    const e = c.win.traceHits(t);
    ok('散文体：三篇来源/本文综合都算痕迹', e.indexOf('本文综合') >= 0 && e.indexOf('这三篇') >= 0, JSON.stringify(e));
    c.$('genreSel').value = 'paper';
    const p = c.win.traceHits(t);
    ok('论文体：放行"本文综合""这三篇"', p.indexOf('本文综合') < 0 && p.indexOf('这三篇') < 0, JSON.stringify(p));
    ok('论文体：碰撞/矛盾轴/撞出仍恒查',
      p.indexOf('碰撞') >= 0 && p.indexOf('矛盾轴') >= 0 && p.indexOf('撞出') >= 0, JSON.stringify(p));
    ok('论文体：干净的学术文本零命中', c.win.traceHits('本文提出一条判据，并给出可证伪条件。').length === 0);
  });

  await step('二十七之五、没有检索 Key：如实说，指路 F 模式，不假装搜过', async () => {
    const c = await boot({ webNoKey: true });
    pickModeD(c);
    c.$('apiKey').value = 'sk-fake';
    c.click('#goBtn');
    await waitFor(() => /用不了|检索/.test(c.$('errBox').textContent), 20000);
    ok('如实报出用不了', /联网检索这一路暂时用不了/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('指路 F 模式', /F 模式/.test(c.$('errBox').textContent));
    ok('没有把三家凑出来', c.win.ST.sources.length === 0, JSON.stringify(c.win.ST.sources.length));
  });

  await step('二十七之六、搜得太少 / 基底给不出成形的源：都如实停下', async () => {
    const c1b = await boot({ webThin: true });
    pickModeD(c1b);
    c1b.$('apiKey').value = 'sk-fake';
    c1b.click('#goBtn');
    await waitFor(() => /撑不起|只搜到/.test(c1b.$('errBox').textContent), 20000);
    ok('搜得太少就说撑不起三个源', /撑不起三个源/.test(c1b.$('errBox').textContent), c1b.$('errBox').textContent);

    const c2 = await boot({
      answer: u => /请从里面挑出\*\*三家现行理论\*\*/.test(u) ? '===源1\n标题：只挑到一家\n===' : defaultAnswer(u)
    });
    pickModeD(c2);
    c2.$('apiKey').value = 'sk-fake';
    c2.click('#goBtn');
    await waitFor(() => /成形的源/.test(c2.$('errBox').textContent), 20000);
    ok('只读出一个源就停下并指路', /只从基底那里读出 1 个成形的源/.test(c2.$('errBox').textContent), c2.$('errBox').textContent);
  });

  await step('二十七之七、拿不到链接时不替它编一个', async () => {
    const c = await boot({
      answer: u => /请从里面挑出\*\*三家现行理论\*\*/.test(u) ? webPickAnswer({ noLink: true }) : defaultAnswer(u)
    });
    pickModeD(c);
    await runPipeline(c, 35000);
    ok('红字点出有几家没拿到链接', /没拿到可点开的链接/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    const wr = c.calls.filter(x => /照下面的目录，把整篇文章/.test(x.user)).pop();
    ok('出处清单如实写"无链接，须自行补"', wr && /无链接，须自行补/.test(wr.user));
    ok('没有凭空造出一个 http 链接', wr && !/https?:\/\/(?!sdeuniverses)/.test((wr.user.match(/【三家的出处[\s\S]{0,600}/) || [''])[0]));
  });
"""


def main():
    h = open(SIM, encoding="utf-8").read()

    # 五种模式了
    h = sub1(h,
             "    ok('四种选源模式都在', c1.doc.querySelectorAll('.mode').length === 4);",
             "    ok('五种选源模式都在（A/B/C/D/F）', c1.doc.querySelectorAll('.mode').length === 5);\n"
             "    ok('模式 D 在（站外三领域·自动检索）', !!c1.doc.querySelector('.mode[data-mode=\"D\"]'));\n"
             "    ok('成品体例两选一', c1.doc.querySelectorAll('#genreSel option').length === 2);",
             "模式数")

    # 假检索端点
    h = sub1(h,
             "      if (url.indexOf('/api/kb/neighbors') >= 0) {",
             """      if (url.indexOf('/api/wds/websearch') >= 0) {
        const q = (JSON.parse(init.body || '{}').q) || '';
        ctx.webQ = (ctx.webQ || []); ctx.webQ.push(q);
        if (opts.webNoKey) return J({ ok: false, reason: 'need_search_key', items: [] });
        if (opts.webThin) return J({ ok: true, reason: '', items: [] });
        return J({ ok: true, reason: '', items: WEB_ITEMS(q) });
      }
      if (url.indexOf('/api/kb/neighbors') >= 0) {""",
             "假检索端点")

    # 假检索结果 + 两个新调令的答复
    h = sub1(h,
             "function defaultAnswer(userMsg) {",
             """/* 假的检索结果：形状照 worker.js 的 webSearch 出参 {t,u,s,m,d} */
function WEB_ITEMS(q) {
  return [0, 1, 2, 3].map(i => ({
    t: '关于「' + q.slice(0, 8) + '」的理论 ' + (i + 1), u: 'https://example.org/paper-' + i,
    s: '这一家主张若干。'.repeat(12), m: '期刊 ' + i, d: '2025-0' + (i + 1) + '-01'
  }));
}
/* 三个成形的源（模式 D 的第二趟产物）。noLink 用来验"拿不到链接时不替它编" */
function webPickAnswer(o) {
  o = o || {};
  const one = (n, disc) => ['===源' + n,
    '标题：' + disc + '的那一家理论',
    '学科：' + disc,
    '出处：某人 2025 · 《某篇》',
    '链接：' + (o.noLink ? '（检索结果里没有）' : 'https://example.org/paper-' + n),
    '论点：这一家认为那件事的病根在' + disc + '这一层。',
    '正文：' + '论证若干句。'.repeat(40)].join('\\n');
  return [one(1, '认知心理学'), one(2, '制度经济学'), one(3, '现象学'), '===',
    '对立点：三家把病根安在三个不同的层上，互相取消对方的前提。'].join('\\n\\n');
}
function defaultAnswer(userMsg) {
  if (/把它拆成\\*\\*三个检索词\\*\\*/.test(userMsg))
    return '1｜认知心理学｜认知负荷 理论 争论\\n2｜制度经济学｜度量 制度 批评\\n3｜现象学｜前反思 身体 理论';
  if (/请从里面挑出\\*\\*三家现行理论\\*\\*/.test(userMsg)) return webPickAnswer();""",
             "假检索结果与答复")

    # pickModeD 辅助
    h = sub1(h,
             "/* 手挑模式：勾上\"我自己挑三篇\"，再勾前三篇 */",
             """/* 模式 D：点 D 卡片、填议题 */
function pickModeD(c) {
  c.click('.mode[data-mode="D"]');
  c.$('dTopic').value = '一个东西被度量之后会怎样';
  c.$('dTopic').dispatchEvent(new c.win.Event('input', { bubbles: true }));
  return 3;
}
/* 手挑模式：勾上"我自己挑三篇"，再勾前三篇 */""",
             "pickModeD")

    # 插入新节
    h = sub1(h,
             "  await step('二十五、全程零运行时错误', async () => {",
             SECTION.strip("\n") + "\n\n  await step('二十五、全程零运行时错误', async () => {",
             "插入二十七节")

    open(SIM, "w", encoding="utf-8").write(h)
    print("patched:", os.path.relpath(SIM, ROOT), len(h), "字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
