#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 tools/sim_paradigm_forge.js 补上近邻三关的覆盖。

三件事：
 ① beforeParse 里注入**真的** sde-rag.js / sde-nbr-gate.js（jsdom 不会自己加载外链脚本）。
    注入真源码而不是替身——判据只有一份来源，替身一写判据就有第二份、且它的漂是静默的。
 ② 假 fetch 加 /api/kb/neighbors 路由（含 nbrFail 开关）。
 ③ 改两条钉在旧措辞上的断言，新增近邻三关的场景。

用法：python3 tools/patch_sim_forge_nbr.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(ROOT, "tools", "sim_paradigm_forge.js")


def sub1(h, old, new, name):
    assert old in h, "锚不到：" + name
    assert h.count(old) == 1, "锚不唯一（%d）：%s" % (h.count(old), name)
    return h.replace(old, new, 1)


def main():
    h = open(SIM, encoding="utf-8").read()

    # ── ① 真模块注入 ──
    h = sub1(h,
             "const HTML = fs.readFileSync(HTML_PATH, 'utf8');",
             "const HTML = fs.readFileSync(HTML_PATH, 'utf8');\n"
             "/* 页面靠两个共用模块干近邻的活，而 jsdom 不加载外链脚本 —— 这里注入**真源码**。\n"
             " * 不写替身：判据一被复制两份就会漂，而那种漂是静默的（一边改了阈值另一边不知道）。 */\n"
             "const ASSETS = path.join(__dirname, '..', 'public', 'taste', 'assets');\n"
             "const RAG_JS = fs.readFileSync(path.join(ASSETS, 'sde-rag.js'), 'utf8');\n"
             "const NBR_JS = fs.readFileSync(path.join(ASSETS, 'sde-nbr-gate.js'), 'utf8');",
             "真模块读入")

    h = sub1(h,
             "      win.fetch = makeFetch();\n",
             "      win.fetch = makeFetch();\n"
             "      // 两个共用模块要在页面脚本之前就位（页面第一次用到它们是在近邻划界那一格）\n"
             "      try { win.eval(RAG_JS); win.eval(NBR_JS); } catch (e) { ctx.errors.push('共用模块注入失败: ' + e.message); }\n",
             "真模块注入")

    # ── ② 假名单端点 ──
    h = sub1(h,
             "      if (url.indexOf('/api/kb/retrieve') >= 0) return opts.kbFail ? BAD(500) : J({ block: '【站内材料】假的检索块' });",
             "      if (url.indexOf('/api/kb/retrieve') >= 0) return opts.kbFail ? BAD(500) : J({ block: '【站内材料】假的检索块' });\n"
             "      if (url.indexOf('/api/kb/neighbors') >= 0) {\n"
             "        if (opts.nbrFail) return BAD(500);\n"
             "        const q = (JSON.parse(init.body || '{}').q) || '';\n"
             "        ctx.nbrQ = (ctx.nbrQ || []); ctx.nbrQ.push(q);\n"
             "        return J({ n: 2, block: NBR_BLOCK(q) });\n"
             "      }",
             "假名单端点")

    # 名单块生成器 + 一份能过闸的划界产物
    h = sub1(h,
             "function defaultAnswer(userMsg) {",
             """/* 端点真产物的形状（worker.js 的 nbBlock）：抬头 + 编号 + 《标题》（链接）｜作者 ｜本人已发 + 那一行判断。
   带一篇「自噬性稳态」那样的近名篇目，好让第三关（成文改了名）有东西可抓。 */
function NBR_BLOCK(q) {
  const near = /拮抗负荷|新命名/.test(q) ? '拮抗负荷的临界' : '自噬性稳态';
  return '【站内近邻（sdeuniverses.com 已发表的相关篇目）——这一节是硬要求：\\n'
    + '对下列每一篇，必须说清它已经说到哪一步，以及你这一次的判断与它的分离线在哪；\\n'
    + '凡划不出分离线的，直接说明本次判断与该篇重复，不要另起新名。】\\n'
    + '1、《' + near + '》（/students/zhang-qiong/x/）｜作者 张琼｜**本人已发**\\n'
    + '　　该篇的判断：系统靠自己吃掉自己维持稳定。\\n'
    + '2、《改不动的机器》（/students/zhang-qiong/y/）\\n'
    + '　　该篇的判断：越是修得动的地方越先被修死。\\n';
}
/* 一份形状齐全、两关都过的划界产物：抬头 + 学科 + 三处点名 + 学科标注 + 判决性预测 */
function demarcOK() {
  return '近邻检测\\n本文所属学科：社会学\\n'
    + '一、可取用困难（Bjork 1994）（学科：认知心理学）｜它说到哪一步：难一点记得牢。｜分离线：本文讲的是那道难度被谁读出来。｜判决性对照预测：若把难度撤掉而效果不变，则本文错。\\n'
    + '二、《规训与惩罚》（学科：哲学）｜它说到哪一步：可见性生产服从。｜分离线：本文讲的是不可见者被判为不存在。｜判决性对照预测：若不可测项照样进入分配，则本文错。\\n'
    + '三、古德哈特定律（Goodhart 1975）（学科：经济学）｜它说到哪一步：度量一旦成目标就变坏。｜分离线：病灶在固定这个动作本身。｜判决性对照预测：若换更好的度量能恢复流失的能力，则本文错。\\n'
    + '四、《自噬性稳态》（学科：社会学）｜它说到哪一步：系统吃自己维稳。｜分离线：本文的是外化-固定，不是自我消耗。\\n'
    + '五、《改不动的机器》（学科：社会学）｜它说到哪一步：修得动的先被修死。｜分离线：本文给的是成因不是现象。\\n'
    + '最近的邻居是古德哈特定律，但它不能吸收本判断：它管的是度量的品质，本文管的是固定这个动作。';
}
/* 缺判决性预测、且六条全在同一学科 —— 两关都该拦下 */
function demarcBad() {
  return '近邻检测\\n本文所属学科：社会学\\n'
    + '一、《自噬性稳态》（学科：社会学）｜侧重不同。\\n'
    + '二、《改不动的机器》（学科：社会学）｜侧重不同。\\n'
    + '三、某个说法（学科：社会学）｜侧重不同。';
}
function defaultAnswer(userMsg) {""",
             "假名单与划界产物")

    # 默认答复：划界那一格给能过闸的产物；涌现那一格带上命名
    h = sub1(h,
             "  if (/你是评审/.test(userMsg)) return '总分：152",
             "  if (/请把它与既有说法逐一划清界线/.test(userMsg)) return demarcOK();\n"
             "  if (/请执行涌现/.test(userMsg)) return '涌现物：命名为「外化固定症」。' + '一句判断撑住它。'.repeat(20);\n"
             "  if (/你是评审/.test(userMsg)) return '总分：152",
             "默认答复补两格")

    # ── ③ 改两条钉在旧措辞上的断言 ──
    h = sub1(h,
             "'划界要 6–10 个近邻并落到可分辨判据'",
             "'划界要 6–10 个近邻、点名 ≥3、落到可分辨判据'",
             "断言一改名")
    h = sub1(h,
             "'划界把站内检索块垫了进去'",
             "'划界把站内语料垫了进去（背景）'",
             "断言二改名")

    open(SIM, "w", encoding="utf-8").write(h)
    print("patched:", os.path.relpath(SIM, ROOT), len(h), "字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
