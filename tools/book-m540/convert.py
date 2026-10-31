#!/usr/bin/env python3
"""第 540 号《文明何以再生》：把 v0.8 统稿三审修订稿（50 章分章母稿）转成 220 版式工具链的分卷稿。只做格式转换，不动正文文字。
产物：front/00-前置.md、parts/01-…08-*.md（八编）、back/09-结语.md、back/10-后置.md、book.md。
用法：python3 tools/book-m540/convert.py
"""
import json, re, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from meta import NO, ISBN, PRICE, PKG, VERDICT  # noqa: E402
P = Path(PKG)
PARTS = [(1, 6, '第一编', '文明为何需要重新肥沃'), (7, 12, '第二编', '中国文明上：从多源形成到思想重构'),
         (13, 18, '第三编', '中国文明下：跨域知识、外部冲击与现代再发生'), (19, 24, '第四编', '西方文明上：多重起源、翻译网络与知识再组织'),
         (25, 30, '第五编', '西方文明下：现代创造力与负面回写的纠缠'), (31, 36, '第六编', '印度文明上：内部异质、帝国伦理与知识生产'),
         (37, 42, '第七编', '印度文明下：跨区域相遇、殖民处境与自主重构'), (43, 50, '第八编', '比较、证明与文明再生的方法')]
CPMETA = [('书名', '《文明何以再生——SDE异质回写肥化原理与中西印文明比较史》'),
          ('英文书名', 'How Civilizations Regenerate: The SDE Principle of Heterogeneous Write-Back and a Comparative History of China, the West and India'),
          ('著者', '王德生　黄倩盈　胡志英'),
          ('执笔', '三位著者署名；文字由 AI（Claude）协作成稿，经统稿、三轮内部审校与编辑终审复核'),
          ('出版', '德麦国际出版社（Demai International Press）· 新加坡'), ('编号', '德麦国际专著第 %d 号' % NO),
          ('ISBN', ISBN), ('定价', PRICE), ('开本', '170 mm × 240 mm'), ('字数', '约 30 万字'), ('版次', '2026 年 10 月第 1 版')]
CPNOTES = [
 'AI 协作声明：本书由王德生、黄倩盈、胡志英署名；文字在著者指令下由 AI（Claude）协作成稿，并经三轮内部审校（事实与出处、理论与论证、全书一致性）及编辑终审复核。该内部审校由同一 AI 助手分轮执行，不等于三名独立专家评审，不替代出版社正式三审三校，也不代著者核签。',
 '史料说明：全书使用 281 项史料台账，正文引用 275 项、730 处编号，见参考书目。重点复核 21 条，不等于 281 项原始全文逐一校勘。原典影印、译本校勘与出版体例的未决事项见附录 A。开篇关于土地三轮长草与翻耕的叙述，是著者的现场观察，未经土壤检测，不作为农业实验或控制对照。',
 '全书结构：出版信息、作者介绍、前言、导读、目录；第一编至第八编（第 1—50 章）；结语、附录 A—B、参考书目。',
 '版权所有　侵权必究']
AUTHOR_BIO = [
 '王德生（Desheng Wang），博士，SIO 本体论与 SDE 发生学创立者。',
 '湘潭大学数学系本科、硕士，中国科学院数学研究所博士，中国科学院计算数学研究所博士后。曾任英国斯旺西大学高级研究员、新加坡南洋理工大学数学系助理教授（博士生导师）与资深研究科学家。在计算数学与图形学国际期刊发表论文 47 篇。',
 '现任德麦国际（Demai International Pte. Ltd.，新加坡）创始人、董事长，主持 SDE Universes 平台（sdeuniverses.com）。',
 '黄倩盈，SDE 学员。自 2019 年起跟随王德生博士学习，经历了从“三视角”到 SIO、再到 SDE 的理论发展；以发生学的视角理解教育、艺术与生活，研究围绕“理解是如何发生的”展开，提出亲证、所依、场先于位等概念；自 2023 年起累计观演百余场；近年关注人工智能与教育的融合。',
 '胡志英（John Hu），约翰英语创始人、攀阁林学院联合创始人，曾任郑州灵答英语执行校长，深耕英语教育与课程创新十三年以上。长期研读乔姆斯基、克拉申等语言学与语言习得理论，并在王德生博士指导下研习三视角语言学、321 智慧与语言发生学；著有《下一步才算数》等 SDE 专著。']
PREFACE = f"""这本书从一块地讲起：同一处土地，坚硬过，长过草，被割过、翻过，又长草，再翻；三轮之后，土显得松了、厚了。著者当时问的不是"文明遵守什么规律"，而是一个更朴素的问题：**前一轮发生，究竟给后一轮留下了什么？**

围绕这个问题，本书用 SDE 的三个方程、六条路径和三条原理，读中国、西方、印度三大文明各自的历史，问同一件事：哪些异质的作用被留下并写回，哪些被过滤掉，下一轮发生的条件因此变肥还是变瘦。全书的判词是：

> {VERDICT}

这句话有三层限制，读者应当先知道。第一，那块地只是问题的来处，没有土壤检测，不作为证据，更不能把"割草"直接翻译成对任何人群的处置。第二，"异质"是关系判断，不是出身证明；本书评价的是具体做法、支配关系和持续后果。第三，本书给出的是有适用条件的命题，并写明什么证据会使它受到挑战，第六章与第四十八章专讲这件事。

全书八编五十章，净正文三十余万汉字。引文均给出史料台账编号，台账附于参考书目；凡原典、影印、译本尚未逐项校勘之处，附录 A 逐条列明，正文没有用它们支撑更强的断言。
"""
GUIDE = """**想先看问题**：读第 1 章，再读第 2、3 章，即固化、异质两个概念。

**想先看方法**：读第 4 章（三方程、六路径、回写）与第 6 章（条件证明）。第 6 章的公式有适用条件，读时请连同条件一起读。

**想先看历史**：第二至第七编分别讲中国、西方、印度各两编，每章围绕一个具体切口，不是通史；它们是对原理的检验，不是对原理的装饰。

**想先看它如何被反驳**：直接读第 48 章《反例与竞争解释》，再读第 50 章《结论》。

阅读时请始终区分三件事：**史料说了什么**、**著者怎样解释**、**这一解释在什么条件下成立**。三者在正文里分开写，不混用。

每章按"一、二、三……"分节。方括号中的编号，如 [R02]，对应参考书目中的史料条目。本书的路线分四步：先说明观察、类比与机制假说的区别（第 1—3 章）；再给出回写如何发生、谁有权判断正面与负面、什么条件下能得出有限结论（第 4—6 章）；然后用三大文明各六章的具体史料检验（第 7—42 章）；最后做跨文明比较，并回到"文明何以学习如何再生"（第 43—50 章）。
"""
CONCL = f"""> {VERDICT}

本书到这里，只证明了一件有限的事：在写明的条件下，把正面回写留下、把负面回写过滤掉，比不过滤更可能使后一轮的条件变好；并且文明的"过滤"不是一把剪刀，而是一组可修订、可问责、被过滤者也能提出异议的安排。

它没有证明的同样重要：三大文明的跨度远大于本书的切口，样本外推、机制与竞争解释的经验限度仍在；书中的数学检查是代数、边界与例值的检查，不是对历史参数的估计。若读者能找到本书所写条件成立、而结论相反的历史案例，那正是本书希望被找到的东西。
"""

# 成书三审补订（只做文字去残留与交叉引用，其余正文不动；每条必须恰好命中一次）
EDITS = [(24, '前文已讨论八六八年汉文《金刚经》印本', '第十章已讨论八六八年汉文《金刚经》印本')]

def chapter(n):
    lines = (P / f'chapters/ch{n:02d}.md').read_text(encoding='utf-8').strip().split('\n')
    m = re.match(r'# 第(\d+)章 (.*)', lines[0]); assert m and int(m[1]) == n, lines[0]
    raw = '\n'.join(lines[1:])
    for k, old, new in EDITS:
        if k == n:
            assert raw.count(old) == 1, (n, old)
            lines = [lines[0]] + raw.replace(old, new).split('\n')
    body = '\n'.join('### ◆ ' + l[3:].strip() if l.startswith('## ') else l for l in lines[1:])
    return '## 第 %d 章　%s\n\n%s\n' % (n, m[2].strip(), re.sub(r'\n{3,}', '\n\n', body).strip())

def main():
    (HERE / 'front').mkdir(exist_ok=True); (HERE / 'parts').mkdir(exist_ok=True); (HERE / 'back').mkdir(exist_ok=True)
    cp = '## 出版信息\n| 项 | 内容 |\n|---|---|\n' + ''.join('| %s | %s |\n' % r for r in CPMETA) + '\n' + '\n\n'.join(CPNOTES)
    au = '## 作者介绍\n\n' + '\n\n'.join(AUTHOR_BIO)
    (HERE / 'front/00-前置.md').write_text(cp + '\n\n' + au + '\n\n## 前言　一块地提出的问题\n\n' + PREFACE + '\n## 导读　这本书怎么读\n\n' + GUIDE, encoding='utf-8')
    names = []
    for k, (a, b, lab, nm) in enumerate(PARTS, 1):
        fn = 'parts/%02d-%s.md' % (k, lab); names.append('%02d-%s' % (k, lab))
        (HERE / fn).write_text('# %s　%s\n\n' % (lab, nm) + '\n'.join(chapter(n) for n in range(a, b + 1)), encoding='utf-8')
    (HERE / 'back/09-结语.md').write_text('# 结语　让历史有权否决\n\n' + CONCL, encoding='utf-8')
    unres = (P / '出版前未决事项.md').read_text(encoding='utf-8').split('\n', 2)[2].strip()
    appx = ('## 附录A　出版前未决事项\n\n' + unres + '\n\n## 附录B　版本与审校说明\n\n本书据 v0.8 统稿三审修订稿成书，五十章正文净 300,984 汉字。三轮内部审校分别查事实出处、理论论证、全书一致性；共记录 129 项修订，其中 44 项内容或表达修订、85 项公历年份写法统一，不等于 129 处史实错误。26 项数学代数、边界与例值检查通过，不等于 26 条新的文明定理。内部审校由同一 AI 助手分轮完成，不等于独立专家评审，也不代作者核签。成书时另做两处补订：参考书目 R01 条原题含对话用语，改为“著者口述记录”；第 24 章一处“前文已讨论”改为明确指向第十章。这两处不改变任何论证。\n')
    led = json.loads((P / '史料台账.json').read_text(encoding='utf-8'))
    def line(r):
        d = r.get('date') or r.get('year', ''); ex = ' DOI:%s。' % r['doi'] if r.get('doi') else ''
        if r['id'] == 'R01':   # 台账原题含对话残留，书中改为著者口述
            return '王德生. 著者关于一块土地三轮长草与翻耕的观察和理论修正（口述记录）. %s.' % d
        u = r.get('url', '')
        us = ' %s' % u if u.startswith('http') else ''
        return '%s. %s. %s.%s%s' % (r.get('author', ''), r.get('title', ''), d, ex, us)
    bib = '# 参考书目\n\n以下为全书史料台账（编号 R01–R281），按编号排列。正文以方括号编号引用。每条的类型、核验范围与限制，见本书网页版“史料台账”（/books/m/%d/references/ledger.json）；条目数量不等于逐条原件校勘。' % NO + '\n\n' + '\n'.join('%d. [%s] %s' % (i + 1, r['id'], line(r)) for i, r in enumerate(led)) + '\n'
    (HERE / 'back/10-后置.md').write_text('# 附录\n\n' + appx + '\n' + bib, encoding='utf-8')
    files = ['front/00-前置.md'] + ['parts/%s.md' % x for x in names] + ['back/09-结语.md', 'back/10-后置.md']
    (HERE / 'book.md').write_text('\n'.join((HERE / f).read_text(encoding='utf-8').strip() + '\n' for f in files), encoding='utf-8')
    han = lambda s: len(re.findall(r'[一-鿿]', s))
    print('ok', names, 'han', han((HERE / 'book.md').read_text(encoding='utf-8')))

if __name__ == '__main__':
    main()
