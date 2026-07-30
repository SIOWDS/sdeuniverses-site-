#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sim 第二刀：修两条钉在旧措辞上的断言 + 新增「二十六、近邻三关」整节。

断言纪律（两条都是这条线上踩出来的）：
  · 钉在承重的那一行，不要整段 grep——整段 grep 抓不到"判据被从闸门里摘掉"这种改法。
  · 共用模块本身也要跑一遍判据，并检查页面确实优先走它（不是页面里另存了一份）。

用法：python3 tools/patch_sim_forge_nbr2.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(ROOT, "tools", "sim_paradigm_forge.js")


def sub1(h, old, new, name):
    assert old in h, "锚不到：" + name
    assert h.count(old) == 1, "锚不唯一（%d）：%s" % (h.count(old), name)
    return h.replace(old, new, 1)


NEW_SECTION = r"""
  /* ============ 二十六、近邻三关 ============
     为什么单开一节：这一页的近邻工序与金点子/中华智问共用同一份判据模块，
     而它多一条自己的规矩——闸门查的是【划界格的产物】而不是成品（成品要零工序痕迹，
     往正文里塞一节叫「近邻检测」的东西恰好是被封禁的那种痕迹）。这一节就是守这条分工的。 */

  await step('二十六、近邻名单：走专用端点、多种子、名单前置于语料', async () => {
    const c = await boot();
    pickModeA(c);
    const done = await runPipeline(c, 30000);
    ok('跑到底', done, c.$('stat-review').textContent);
    const de = c.calls.filter(x => /划清界线/.test(x.user)).pop();
    ok('划界调令拿到的是名单（不只是语料）', de && /站内近邻（sdeuniverses\.com 已发表的相关篇目）/.test(de.user));
    ok('名单前置在语料之前（放后面会被语料埋掉）',
      de && de.user.indexOf('站内近邻（sdeuniverses') < de.user.indexOf('站内可参照的语料'));
    ok('打的是专用端点 /api/kb/neighbors', (c.nbrQ || []).length >= 1, JSON.stringify(c.nbrQ));
    ok('多种子：判断与命名各查一个角度', (c.nbrQ || []).length >= 2, JSON.stringify(c.nbrQ));
    ok('命名单独当过种子（概念名常只在副标题/关键词里，用话题查召回不到）',
      (c.nbrQ || []).some(q => /外化固定症/.test(q)), JSON.stringify(c.nbrQ));
    ok('名单里「本人已发」的标注带进去了', de && /本人已发/.test(de.user));
  });

  await step('二十六之二、划界调令要可解析的形状（想让什么被检查，先让它有个形状）', async () => {
    const c = await boot();
    pickModeA(c);
    await runPipeline(c, 30000);
    const de = c.calls.filter(x => /划清界线/.test(x.user)).pop();
    ok('第一行钉「近邻检测」', de && /第一行必须是：近邻检测/.test(de.user));
    ok('第二行钉「本文所属学科」', de && /第二行必须是：本文所属学科/.test(de.user));
    ok('每条要「（学科：XXX）」标注', de && /（学科：XXX）/.test(de.user));
    ok('至少 3 个点到名（作者年份 或《作品》）', de && /至少 3 个必须点到名/.test(de.user));
    ok('至少一个来自本文学科之外', de && /至少一个必须来自本文学科之外/.test(de.user));
    ok('每条要判决性对照预测', de && /判决性对照预测/.test(de.user) && /若……则本文错/.test(de.user));
    ok('明说这是引擎室中间产物、成品会改写成散文', de && /引擎室的中间产物/.test(de.user) && /改写成散文/.test(de.user));
  });

  await step('二十六之三、两关就地过：达标时状态条如实报', async () => {
    const c = await boot();
    pickModeA(c);
    await runPipeline(c, 30000);
    ok('划界格标为达标', /划界达标/.test(c.$('stat-demarc').textContent), c.$('stat-demarc').textContent);
    ok('交付横幅报了过闸', /近邻划界已过闸/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
  });

  await step('二十六之四、关一/关三不过：默认停下让用户决定，不自动重跑，也不阻断交付', async () => {
    const c = await boot({ answer: u => /划清界线/.test(u) ? demarcBad() : defaultAnswer(u) });
    pickModeA(c);
    const done = await runPipeline(c, 30000);
    const demarcCalls = c.calls.filter(x => /划清界线/.test(x.user)).length;
    ok('划界只跑了一趟（默认不自动重跑）', demarcCalls === 1, '跑了 ' + demarcCalls + ' 趟');
    ok('状态条标出没过闸', /⚠/.test(c.$('stat-demarc').textContent), c.$('stat-demarc').textContent);
    ok('红字点名是哪一关没过', /判决性对照预测|同一学科/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('红字给出三条口子（重跑/编辑/照走）', /重跑本格/.test(c.$('errBox').textContent) && /由你决定/.test(c.$('errBox').textContent));
    ok('照样跑到底、照样交付', done, c.$('stat-review').textContent);
    ok('交付横幅把没过闸也报出来', /近邻划界：/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
  });

  await step('二十六之五、勾了自动重跑：不过闸就重跑那一格（只重跑一次）', async () => {
    const c = await boot({ answer: u => /划清界线/.test(u) ? demarcBad() : defaultAnswer(u) });
    c.$('autoRedoChk').checked = true;
    pickModeA(c);
    const done = await runPipeline(c, 40000);
    const demarcCalls = c.calls.filter(x => /划清界线/.test(x.user)).length;
    ok('划界重跑了一趟', demarcCalls === 2, '跑了 ' + demarcCalls + ' 趟');
    ok('不会无限重跑', demarcCalls <= 2, '跑了 ' + demarcCalls + ' 趟');
    ok('照样跑到底', done, c.$('stat-review').textContent);
  });

  await step('二十六之六、名单取不到：如实说一句、照样跑到底（不静默当做做过了）', async () => {
    const c = await boot({ nbrFail: true });
    pickModeA(c);
    const done = await runPipeline(c, 30000);
    ok('横幅如实说名单没取到', /近邻名单未取到|没上桌/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
    ok('照样跑到底（名单缺失不该让整格失败）', done, c.$('stat-review').textContent);
    const de = c.calls.filter(x => /划清界线/.test(x.user)).pop();
    ok('划界照做（调令仍在）', de && /划清界线/.test(de.user));
  });

  await step('二十六之七、关二：成品改了名就重查，点名未交代的篇目', async () => {
    // 划界那一格照「外化固定症」查过；成品里却管它叫「拮抗负荷症」——等于没查
    const c = await boot({
      answer: u => {
        if (/划清界线/.test(u)) return demarcOK();
        if (/照下面的目录，把整篇文章/.test(u))
          return '本文将这一现象命名为「拮抗负荷症」。' + '正文若干句，够长，末尾有句号。'.repeat(700);
        return defaultAnswer(u);
      }
    });
    pickModeA(c);
    const done = await runPipeline(c, 30000);
    ok('抓住了改名', /拮抗负荷症/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('拿新名字重查过一遍', (c.nbrQ || []).some(q => /拮抗负荷症/.test(q)), JSON.stringify(c.nbrQ));
    ok('点名了未交代的站内篇目', /《/.test(c.$('errBox').textContent), c.$('errBox').textContent);
    ok('横幅也记一笔', /篇近邻未交代/.test(c.$('doneBanner').textContent), c.$('doneBanner').textContent);
    ok('默认不自动重写（是否重跑由用户定）',
      c.calls.filter(x => /照下面的目录，把整篇文章/.test(x.user)).length === 1);
    ok('照样交付', done, c.$('stat-review').textContent);
  });

  await step('二十六之八、关二自动档：带着那些篇目重写一遍，且当散文写、不许另起一节', async () => {
    const c = await boot({
      answer: u => {
        if (/划清界线/.test(u)) return demarcOK();
        if (/照下面的目录，把整篇文章/.test(u))
          return '本文将这一现象命名为「拮抗负荷症」。' + '正文若干句，够长，末尾有句号。'.repeat(700);
        return defaultAnswer(u);
      }
    });
    c.$('autoRedoChk').checked = true;
    pickModeA(c);
    await runPipeline(c, 45000);
    const wr = c.calls.filter(x => /照下面的目录，把整篇文章/.test(x.user));
    ok('成文重写了一趟', wr.length === 2, '跑了 ' + wr.length + ' 趟');
    ok('重写调令点名了那些篇目', wr.length > 1 && /《/.test(wr[1].user));
    ok('明令当散文写、不许另起一节（成品要零工序痕迹）',
      wr.length > 1 && /当散文写/.test(wr[1].user) && /不许另起一节/.test(wr[1].user));
  });

  await step('二十六之九、评审拿到名单去核对（它有 I 封顶 130 那条铁律）', async () => {
    const c = await boot();
    pickModeA(c);
    await runPipeline(c, 30000);
    const rv = c.calls.filter(x => /你是评审/.test(x.user)).pop();
    ok('评审调令附了名单', rv && /站内近邻（sdeuniverses/.test(rv.user));
    ok('名单里没被交代的要扣分', rv && /名单里没被交代的篇目每一篇再减 2/.test(rv.user));
  });

  await step('二十六之十、共用模块本身跑一遍判据，且页面确实优先走它', async () => {
    const c = await boot();
    const G = c.win.SDENbr;
    ok('共用模块已加载（页面不另存一份判据）', !!G && typeof G.sectionOK === 'function');
    if (G) {
      ok('关一：形状齐全的划界产物过', G.sectionOK(demarcOK()) === true);
      ok('关一：缺判决性预测的不过', G.sectionOK(demarcBad()) === false);
      ok('关三：全挤在同一学科 → false', G.crossOK(demarcBad()) === false);
      ok('关三：跨了学科 → true', G.crossOK(demarcOK()) === true);
      ok('关三：看不出 → null（放行，冤枉好文章的代价更大）', G.crossOK('一段没有学科标注的普通文字。') === null);
      ok('抽命名认得出「命名为「X」」', G.coinedName('本文将这一现象命名为「外化固定症」。') === '外化固定症');
    }
    // 钉在承重那一行：闸门必须是问模块要的判定，不是页面自己算的
    ok('页面的闸门钉在 window.SDENbr 上', /const G = window\.SDENbr;/.test(HTML));
    ok('模块没加载就整关跳过（不是当成没过）', /if\(G\)\{[\s\S]{0,400}sectionOK/.test(HTML));
    ok('第三关抽的是成品里的名字', /G\.coinedName\(ST\.article\)/.test(HTML));
  });
"""


def main():
    h = open(SIM, encoding="utf-8").read()

    # 修两条旧断言的正则（措辞已改，判据要跟着钉到新的承重词上）
    h = sub1(h,
             "    ok('划界要 6–10 个近邻、点名 ≥3、落到可分辨判据', de && /6–10 个/.test(de.user) && /判据差在哪/.test(de.user));\n"
             "    ok('划界把站内语料垫了进去（背景）', de && /站内可参照的近邻材料/.test(de.user));",
             "    ok('划界要 6–10 个近邻、点名 ≥3、落到可分辨判据',\n"
             "      de && /6–10 个/.test(de.user) && /至少 3 个必须点到名/.test(de.user) && /可分辨的差别/.test(de.user));\n"
             "    ok('划界把站内语料垫了进去（背景）', de && /站内可参照的语料/.test(de.user));",
             "两条旧断言")

    # 新节插在「二十五、全程零运行时错误」之前
    h = sub1(h,
             "  await step('二十五、全程零运行时错误', async () => {",
             NEW_SECTION.strip("\n") + "\n\n  await step('二十五、全程零运行时错误', async () => {",
             "插入二十六节")

    open(SIM, "w", encoding="utf-8").write(h)
    print("patched:", os.path.relpath(SIM, ROOT), len(h), "字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
