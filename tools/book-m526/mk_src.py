#!/usr/bin/env python3
"""第 526 号《秩序独大》：把三审统稿后的分章稿（unit00_preface.md、unit01—unit10.md）装成 convert.py 认的 src/。
只改标题层级与章题写法，不动正文文字：
  章题「# 第一章 T」→「# 第一章　T」；节「## 一、T」→「## T」（convert 重新编号）；小节「### （一）T」→「#### （一）T」；
  「## 本章引用文献」→「## 本章参考文献」；删去「（第X编 …）」编名行；各编首章前插入编题与编序。
用法：python3 tools/book-m526/mk_src.py <统稿目录>
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
SRC = HERE / 'src'
D = Path(sys.argv[1])

PARTS = {
    1: ('第一编　差异进不来', [
        '门槛只放干净的、可计量的、已经成形的东西进来。这一编看的是第一处断点：新的差异还没来得及与已有的底子发生冲突，就已经被挡在门外，冲突无从累积。',
        '第一章在组织里看这道门槛：评审与审计怎样从一个仍在发生的价值过程里切走骨头，误差、冗余、亏损三项最小化怎样在三十年里一点点溶掉组织可以偏离的余地。第二章把镜头推进到个人与职业判断的内部：评价制度把信道压窄之后，学习者理性地停在庇护所里，法官的判断器官在格式、审级与效率之下逐件干涸。两章合起来说明，差异进不来，不是因为谁拒绝它，而是因为门槛做得太好。']),
    3: ('第二编　结论封口', [
        '差异进了门，却无处落脚，因为落脚的地方已经被答案占满。这一编看的是第二处断点：既有的形态被锁成终端，对一切质疑都有现成的回答，冲突逼不动它。',
        '第三章从诊断与案卷入手，看特征怎样喂饱认知者、饿死被认知的活物；第四章把冷的数字秩序（大学排名）与暖的意义秩序（五行烹饪）放在一起，说明它们凭证相反，却以同一种方式让检验失去位置。由此可以看清，独大的不只是冷的量化，善意与认同同样可以独大。']),
    5: ('第三编　回写变成清场', [
        '秩序的成功会反过来改写它所站立的底子。这一编看的是第三处断点：改写发生了，而且成功地发生了，只是改写出来的底子里，已经没有了下一轮冲突可以长出来的东西。',
        '第五章在认识层面看维持与退场：客观性是每天耗电的火，维持越成功，验证的碰触越稀；“给出原因”的管辖力被抽空，取现成替代了自己去抠。第六章在文明与社会修复层面看依赖清场与制度性自体免疫。第七章下到主体内部：外部的定价被内化为选择者自己的取舍习惯，门由人自己从里面关上。']),
    8: ('第四编　门的重开', [
        '前三编写门怎样被关死，这一编写门怎样重新打开。',
        '第八章写三处破口：教师的失守、等待权的丧失、最优化的用尽，秩序断电的那一刻，挡在门外的差异与关系重新进入；也写破口为什么不能被浪漫化。第九章回答全书留下的问题：门是否只能等崩溃来撞开。它的回答是，破口不可设计，接住可以设计；秩序可以从封闭秩序转为可靠秩序，自己保留一道承接之门。']),
}


def fix(text, chapter=False):
    out = []
    inref = False
    for l in text.splitlines():
        s = l.rstrip()
        if re.match(r'^（第.编 .+）$', s.strip()):
            continue
        m = re.match(r'^## (?:[一二三四五六七八九十]+、)?(.*)$', s)
        if s.startswith('#'):
            inref = '引用文献' in s or '参考文献' in s
        if inref and s.strip() and not s.startswith('#'):
            out += [re.sub(r'^[-*]\s+', '', s.strip()), '']; continue
        if s.startswith('## '):
            t = m[1].strip()
            if t in ('本章引用文献', '参考文献'):
                t = '本章参考文献'
            out.append('## ' + (t if chapter else s[3:].strip().replace('本章引用文献', '本章参考文献')))
            continue
        if s.startswith('### '):
            out.append('#### ' + s[4:].strip()); continue
        if s.startswith('#### '):
            out.append('#### ' + s[5:].strip()); continue
        out.append(s)
    return '\n'.join(out).strip() + '\n'


SRC.mkdir(exist_ok=True)
# 前言
pre = (D / 'unit00_preface.md').read_text()
(SRC / 'qianyan.md').write_text(fix(pre))
# 导论、结语
u1 = (D / 'unit01.md').read_text()
k = u1.index('# 结语')
dl, jy = u1[:k], u1[k:]
dl = re.sub(r'^# 导论 ', '# 导论　', dl)
jy = re.sub(r'^# 结语 ', '# 结语　', jy)
(SRC / 'daolun.md').write_text(fix(dl))
(SRC / 'jieyu.md').write_text(fix(jy))
# 九章
for i in range(1, 10):
    t = (D / ('unit%02d.md' % (i + 1))).read_text()
    t = re.sub(r'^# (第[一二三四五六七八九]章) ', r'# \1　', t, flags=re.M)
    body = fix(t, chapter=True)
    if i in PARTS:
        ttl, paras = PARTS[i]
        body = '## %s\n\n%s\n\n' % (ttl, '\n\n'.join(paras)) + body
    (SRC / ('ch%02d.md' % i)).write_text(body)
print('ok', sorted(p.name for p in SRC.iterdir()))
