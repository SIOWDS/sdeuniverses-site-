#!/usr/bin/env python3
"""第 542 号《知识同一性谱系递归发生学》：把 v0.6 统稿三审稿（manuscript/00–42，九编四十一章）转成 220 版式工具链的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、front/01-导论.md（绪论）、parts/01-…09-*.md（九编）、back/09-结语.md（结论）、back/10-后置.md、figs/*.png、book.md。
用法：python3 tools/book-m542/convert.py
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from meta import NO, ISBN, PRICE, PKG, VERDICT, TITLE, SUBTITLE, TITLE_EN  # noqa: E402
P = Path(PKG)
CN = {c: i for i, c in enumerate('零一二三四五六七八九', 0)}


def cn2int(s):
    if '十' in s:
        a, _, b = s.partition('十'); return (CN[a] if a else 1) * 10 + (CN[b] if b else 0)
    return CN[s]


CPMETA = [('书名', '《%s——%s》' % (TITLE, SUBTITLE)), ('英文书名', TITLE_EN), ('著者', '王德生'),
          ('执笔', '著者提出理论与框架；文字由 AI（Claude）在著者指令下协作续写、统稿，经三轮内部审校'),
          ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % NO),
          ('ISBN', ISBN), ('定价', PRICE), ('开本', '170 mm × 240 mm'), ('字数', '正文净 299,079 汉字（约 30 万字）'), ('版次', '2026 年 10 月第 1 版')]
CPNOTES = [
 'AI 协作声明：本书署名王德生；全书的理论框架与问题由著者提出，文字在著者指令下由 AI（Claude）协作续写、统稿，并经三轮内部审校（来源与证据、概念与论证、结构与术语）。三轮审校由同一模型家族的助手分段执行，不是三名独立专家的评审，不替代出版社正式三审三校，也不代著者核签。',
 '来源说明：全书使用 121 项来源，逐项登记了实际读取范围与使用边界（见参考书目与随书的来源台账）。多数来源只读到摘要、工作稿或部分页面，没有一项可以理解为被全文通读，更不意味着它单独支持了本书的整条论证。',
 '数值与实验说明：书中所有数值算例均为思想实验或固定种子的构想模拟，不是现实数据；所有关于思想复合主体、工具迁移、经济指标的研究设计均未执行，书内没有任何实验结果；附录与第 33 章提到的检查程序只验证有限构造，不是一般命题的证明。',
 '全书结构：出版信息、作者介绍、前言、导读、目录；绪论；第一编至第九编（第 1—41 章）；结论、附录 A—B、参考书目。',
 '版权所有　侵权必究']
AUTHOR_BIO = [
 '王德生（Desheng Wang），博士，SIO 本体论与 SDE 发生学创立者。',
 '湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后。曾任英国斯旺西大学高级研究员、新加坡南洋理工大学数学系助理教授（博士生导师）与资深研究科学家。在计算数学与图形学国际期刊发表论文 47 篇。',
 '现任德麦国际（Demai International Pte. Ltd.，新加坡）创始人、董事长，主持 SDE Universes 平台（sdeuniverses.com）。']
PREFACE = f"""这本书从一个看起来很熟的问题开始：工具为什么会改变行业？最顺手的回答是"效率提高了"。可是效率提高以后，同行都用上了同样的工具，大家只是在同一个比较方式里跑得更快，并没有走出原来的行业。真正需要解释的，是另一种变化：旧领域的边界变了，原来不能单独组织的活动成了一种服务，一种服务又长出新的职业、组织和市场。

沿着这个问题往前走，书里依次遇到几件事。工具起作用的不是孤立的工具，而是人和工具构成的复合主体；人和人工智能长期共同做研究，还会形成一种特殊的思想复合主体；知识之间的"同一"并不是一个数，而是随任务而变的多维关系；有了大模型之后，谱系里过去无力进入的位置第一次有了被系统填充的可能，而填充所依赖的坐标轴本身也会被改写。全书把最后这一层叫做**递归发生**，并全部用 SDE 的语言来讲：S 是显露，D 是差异序列，E 是特征纠缠系统。

全书的核心定义只有一句，在绪论里：

> {VERDICT}

这句话有三层限制，读者应当先知道。第一，本书的数值例子都是构想出来的思想实验，书内没有新增任何真实的宏观数据，更没有执行任何实验。第二，书中的数学部分是有适用条件的命题和有限复算，不是对一般情形的证明，也不能拿来冒充对全部知识谱系的完备描述。第三，三位一体的出版、版本协议和知识发生平台，在书里一律停在"设计"这一层，不是已经实现的功能。

全书九编四十一章，净正文近三十万汉字。凡引用的来源都给出台账编号，台账写明读取范围；凡尚未核实之处，附录 A 逐条列明。书稿由 AI 协作成稿，审校由同一类助手分轮完成，独立专家的评审和著者的最终核签仍未发生，读者在引用时请把这一点算进去。
"""
GUIDE = """**想先看问题**：读绪论，再读第 1 章（效率提高为什么不一定带来行业升级）。

**想先看历史对照**：第 5—14 章是十类工具的对照，每章分开写"史料说了什么"和"本书的解释"，并列出机制相近而结果不同的反例。

**想先看论证是否严格**：直接读第 24、25、33 章，并对照各章末的边界说明；第 33 章附有依赖图。

**想先看怎样做研究**：从第 21、37 章的设计读起，再读第 38—40 章的接口和平台设计。这些全是设计，不是已实现的结果。

正文中方括号里的编号，如 [R02]，指向来源台账。台账不只写出处，还写明作者实际读取了哪一部分、该来源不能支持什么；看到一个编号，不要理解为这份文献被全文读过。结论一章用同一套区分，把绪论里的六项主张逐项对账：哪些已定义、哪些有限推导、哪些有历史支持、哪些仍待检验。

阅读时请始终区分三件事：**来源说了什么**、**本书怎样解释**、**这一解释在什么条件下成立**。
"""
APPX_A = """本节是出版前仍未闭合的事项清单，不是已完成评审的证明。编号沿用接续包中的 U01—U10。

**U01　篇幅与论证深度。** 正文 299,079 汉字，距 30 万字目标尚差 921 字，没有为凑数而补写。是否扩写由著者决定。独立专家对论证深度的确认尚未发生。

**U02　十大工具史的机制证据。** 已补有来源的时间线、对照与负例（福特与丰田、重犁、卡尼什、红海航行、印刷、蒸汽、电动机、汽车、航空邮运、联网服务、人工智能研究）。多数来源只读到摘要或工作稿；R43、R18 等入口受限，须通过合法的机构版本补核。

**U03　宗教与医学的比较。** 第 16 章以四个原文个案、第 17 章以针刺试验与青蒿素叙述两个具体比较任务写成，不裁决信仰，不含诊疗建议。须由相应传统与语文专家、临床研究方法专家审查。

**U04　思想复合主体的实证地位。** 识别条件、非劣性设计、创始人离场与后继者反驳协议都已写成方案；全部实验未执行，没有任何结果。需要安排独立评审，不能由同一系统的多个角色替代。

**U05　数学证明、原创性与一般化。** 有限复算全部通过；第 33 章命题四至七、零失败审计界等标准推理的文献出处，第 26 章若干经典结论的出处，仍标〔待核〕。须由独立数学审查逐项检查定义、量词、适用域与证明。

**U06　经济增量的识别。** 已补官方指标对应、核算分解、反例、非谱系路线对照与预注册草案 0.1。书内没有任何真实数据；R217—R221 只读摘要，须经济学方法专家复核。

**U07　文献逐项充分性。** 仍未闭合。新来源读取范围逐项登记，未全文通读者已标注；多处页码或细节待著者核对。

**U08　语义重复与正面论证比例。** 部分处理（已合并第 41 章、第 24 章的重复论证）；第 20/21、23、28、34 章仍有小节交叠，留待著者取舍。

**U09　平台设计与现实实现。** 第 39—41 章全部停在"设计"。本书作为出版单元（阅读、学习包、智能体）上站，是一次原型性的发布，学习包与智能体均未做学习效果或真实对话质量的实测。

**U10　正式交付边界。** 已执行三轮专项审校、字数与引用审计、版面渲染检查。独立同行评审与著者审定仍未完成。
"""
APPX_B = """本书据 v0.6 统稿三审稿成书。正文净 299,079 汉字（计数规则：Unicode 区间 U+3400—U+9FFF，不含各级标题行；方括号编号不含汉字）。较接续基线 v0.5（208,681 汉字）增加约 9 万字，来源登记由 43 条增至 121 条，论断台账由 74 条增至 253 条。

三轮内部审校分别查来源与证据地位、概念与证明、结构与术语。审校发现并改正的问题，包括个别来源用法超出读取范围、若干数学定义中符号两义、纯替代公式缺少增加值率、算例缺基线、节号顺延造成的交叉引用错误等。全部复算只验证有限构造和固定种子的构想模型，不是一般命题的认证，也不是现实实验。

审校由同一模型家族的助手分角色、分段执行，各角色的校准题为自答。这不等于独立专家评审，不等于出版社三审三校，也不代著者核签。校验和只验证文件未变，不验证学术真理。著者保留全部最终学术判断权。

正文第 26、33 章等提到的检查程序（scripts/ 目录下的 Python 脚本及其输出）随书公开，见本书网页的“检查程序”目录；它们只使用标准库，固定随机种子。
"""


def render_mermaid(code, tag):
    d = HERE / 'figs'; d.mkdir(exist_ok=True)
    png = d / ('%s_%s.png' % (tag, hashlib.md5(code.encode()).hexdigest()[:8]))
    if not png.exists():
        src = d / 'tmp.mmd'; src.write_text(code, encoding='utf-8')
        cfg = d / 'pp.json'; cfg.write_text('{"args":["--no-sandbox"]}')
        subprocess.run(['mmdc', '-i', str(src), '-o', str(png), '-s', '3', '-b', 'white', '-p', str(cfg)], check=True, capture_output=True)
        src.unlink(); cfg.unlink()
    return png


def chapter_body(raw, n, tag):
    """## 小节 → ### ◆ 小节；mermaid 围栏 → 图片行（!FIG 路径|图注）。"""
    out, infence, buf = [], False, []
    for l in raw.split('\n'):
        if l.startswith('```'):
            if not infence:
                infence = l[3:].strip(); buf = []
            else:
                if infence == 'mermaid':
                    png = render_mermaid('\n'.join(buf), 'ch%02d' % n)
                    out.append('!FIG figs/%s|第 %d 章依赖图：各命题使用的前提（箭头只表示使用关系）' % (png.name, n))
                else:
                    out += ['```'] + buf + ['```']
                infence = False
            continue
        if infence:
            buf.append(l); continue
        out.append('### ◆ ' + l[3:].strip() if l.startswith('## ') else l)
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip()


def load_chapters():
    chs = {}
    for f in sorted((P / 'manuscript').glob('*.md')):
        txt = f.read_text(encoding='utf-8').strip().split('\n')
        m = re.match(r'# 第([一二三四五六七八九十]+)章[　 ]+(.*)', txt[0])
        if m:
            n = cn2int(m[1]); chs[n] = (m[2].strip(), '\n'.join(txt[1:]).strip(), m[1])
    return chs


def main():
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
        for x in (HERE / d).glob('*.md'): x.unlink()
    chs = load_chapters(); assert sorted(chs) == list(range(1, 42)), sorted(chs)
    # 编的划分与名称：取接续包 parts/ 的九编文件
    PARTS = []
    for f in sorted((P / 'parts').glob('0[1-9]_*.md')):
        t = f.read_text(encoding='utf-8')
        h = t.strip().split('\n')[0]
        m = re.match(r'# (第[一二三四五六七八九十]+编)[　 ]+(.*)', h); assert m, h
        ns = [cn2int(x) for x in re.findall(r'^# 第([一二三四五六七八九十]+)章', t, re.M)]
        PARTS.append((ns[0], ns[-1], m[1], m[2].strip()))
        assert ns == list(range(ns[0], ns[-1] + 1)), (h, ns)
    assert len(PARTS) == 9 and PARTS[0][0] == 1 and PARTS[-1][1] == 41, PARTS
    assert all(PARTS[i][1] + 1 == PARTS[i + 1][0] for i in range(8)), PARTS
    cp = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in CPMETA) + '\n' + '\n\n'.join(CPNOTES)
    au = '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_BIO)
    (HERE / 'front/00-前置.md').write_text(cp + '\n\n' + au + '\n\n## 前言　一个问题，和它的边界\n\n' + PREFACE + '\n## 导读　这本书怎么读\n\n' + GUIDE, encoding='utf-8')
    # 绪论
    s0 = (P / 'manuscript/00_绪论.md').read_text(encoding='utf-8').strip().split('\n')
    m0 = re.match(r'# 绪论[　 ]+(.*)', s0[0]); assert m0
    (HERE / 'front/01-导论.md').write_text('# 绪论　%s\n\n%s\n' % (m0[1].strip(), chapter_body('\n'.join(s0[1:]), 0, 'intro')), encoding='utf-8')
    names = []
    for k, (a, b, lab, nm) in enumerate(PARTS, 1):
        fn = 'parts/%02d-%s.md' % (k, lab); names.append('%02d-%s' % (k, lab))
        body = '\n'.join('## 第 %d 章　%s\n\n%s\n' % (n, chs[n][0], chapter_body(chs[n][1], n, 'ch')) for n in range(a, b + 1))
        (HERE / fn).write_text('# %s　%s\n\n' % (lab, nm) + body, encoding='utf-8')
    s42 = (P / 'manuscript/42_结论.md').read_text(encoding='utf-8').strip().split('\n')
    m42 = re.match(r'# 结论[　 ]+(.*)', s42[0]); assert m42
    (HERE / 'back/09-结语.md').write_text('# 结论　%s\n\n%s\n' % (m42[1].strip(), chapter_body('\n'.join(s42[1:]), 42, 'concl')), encoding='utf-8')
    led = json.loads((P / 'sources/registry.json').read_text(encoding='utf-8'))
    key = lambda r: int(re.sub(r'\D', '', r['id']))
    led.sort(key=key)
    def line(r):
        u = r.get('url', ''); us = ' %s' % u if u.startswith('http') else (' %s' % u if u else '')
        return '%s. %s. %s.%s' % (r['author'].rstrip('.'), r['title'].rstrip('.'), r['publication'].rstrip('.'), us)
    bib = '# 参考书目\n\n以下为全书来源台账（%d 项，编号 R01–R244 段内不连续），按编号排列，正文以方括号编号引用。每条的读取范围与使用边界见本书网页版“来源台账”（/books/m/%d/references/ledger.json）；条目数量不等于逐条原件校勘，没有一项可以理解为被全文通读。' % (len(led), NO) + '\n\n' + '\n'.join('%d. [%s] %s' % (i + 1, r['id'], line(r)) for i, r in enumerate(led)) + '\n'
    (HERE / 'back/10-后置.md').write_text('# 附录\n\n## 附录A　出版前未决事项\n\n' + APPX_A + '\n## 附录B　版本与审校说明\n\n' + APPX_B + '\n' + bib, encoding='utf-8')
    files = ['front/00-前置.md', 'front/01-导论.md'] + ['parts/%s.md' % x for x in names] + ['back/09-结语.md', 'back/10-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in files), encoding='utf-8')
    json.dump(PARTS, open(HERE / 'parts.json', 'w'), ensure_ascii=False)
    han = lambda s: len(re.findall(r'[一-鿿]', s))
    body = sum(han('\n'.join(l for l in (P / 'manuscript' / f.name).read_text(encoding='utf-8').split('\n') if not l.startswith('#'))) for f in (P / 'manuscript').glob('*.md'))
    print('ok', names, 'book.md han', han((HERE / 'book.md').read_text(encoding='utf-8')), 'manuscript body han', body)


if __name__ == '__main__':
    main()
