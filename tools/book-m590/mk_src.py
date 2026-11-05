#!/usr/bin/env python3
"""第 590 号《每一环都替对了》：把三审统稿后的分章稿（preface.md、intro.md、ch01—ch10.md、conclusion.md、appendix.md）
装成 convert.py 认的 src/（qianyan、daolun、ch01—ch10、jieyu、fulu1）。只改标题层级，不动正文文字：
  章题「# 第一章　T」保留；节「## 一、T」→「## T」（convert 重新编号）；小节「### （一）T」→「#### （一）T」；
  各编首章前插入编题与编序；第十章单独成第四编。
用法：python3 tools/book-m590/mk_src.py <统稿目录>
"""
import re, sys
from pathlib import Path
HERE = Path(__file__).parent
SRC = HERE / 'src'
D = Path(sys.argv[1])

PARTS = {
    1: ('第一编　感知：收不到的身体', [
        '回路的第一环，是身体的信号能不能被自己收到、分辨、说出来。这一编追踪感知环怎样一步步离开主体：先被代劳，再在闲置中萎缩，最后被固化成终局。',
        '第一章看代劳从哪里开始：外部测量替身体说话，一个只承认明确陈述的文明把身体的模糊判成缺陷，于是诞生了翻译义务，内感能力被逐次征税。第二章看萎缩怎样发生：信号被代收、判断被代理、功能被卸载，感知枢纽的精度在长期不被调用中退降，机体对自身失衡“听而不闻”。第三章把镜头移到运动医学：降级的传感器在一次“成功的康复”里通过全部测试，被固化成不可逆的结算状态。三章合起来说明，收不到身体，不是因为谁失职，而是因为每一次测量都做对了。']),
    4: ('第二编　判断：不敢判的身体', [
        '感知被代收之后，判断也就跟着被代理。这一编看回路的第二环：收到以后，能不能、敢不敢由自己做出裁量。',
        '第四章写一位模范患者的裁决力怎样在完全依从、完全有能力、完全不反抗的状态下退场，并提出低效冗余作为裁决回路再培育的微生态。第五章再推一步：不只是谁来裁定，“修好了没有”这个裁定动作本身就打断了修复的自主节律。第六章揭示最隐蔽的一层：代劳者不只来自外部，身体自己过去的成功代偿也会结算成一套自动判决，忠实执行全部旧判决，封死一切新判决。']),
    7: ('第三编　重组：不会自己组织的身体', [
        '回路的第三环，是扰动来了，身体能不能自己把一次失调完整走完，重新组织出秩序。这一编看重组环怎样被截走、被闲置、被锁死。',
        '第七章命名拮抗负荷：保护性干预在系统仍能自己应对时提前接管，取走的不是一次伤害，而是一次完整穿越扰动的时序信号。第八章提出构成性时序：内源组织能力只能在每一次未被代偿的完整时序里被重新构成，否则身体陷入“指标正常、能力塌陷”的闲置性病理。第九章走到极限：旧秩序被击溃、一切正确参照失效的时刻，身体怎样凭即时的功能探试重组可行秩序，又怎样被锁死在保守的配置上。']),
    10: ('第四编　归还：把那一程还给身体', [
        '前三编各自走完了回路的一环。这一编只有一章，回答全书留下的问题：既然三环各有损失，为什么不能一环一环地修？',
        '第十章论证三环缠绕在一起、彼此是对方的前提，单环修复必然失败；前九章留下的两类出路——静默与摩擦——表面相反，实则互为条件：静默是条件，摩擦是内容。由此提出整程归还，划定它的安全边界，并把全书分散的证伪条件统一为一个可以推翻本书的检验纲领。']),
}


def fix(text, chapter=False):
    out = []
    inref = False
    for l in text.splitlines():
        s = l.rstrip()
        if s.startswith('#'):
            inref = '参考文献' in s
        if inref and s.strip() and not s.startswith('#'):
            out += [re.sub(r'^[-*]\s+', '', s.strip()), '']; continue
        if s.startswith('## '):
            t = s[3:].strip()
            if chapter:
                t = re.sub(r'^[一二三四五六七八九十]+、', '', t)
            out.append('## ' + t)
            continue
        if s.startswith('### '):
            out.append('#### ' + s[4:].strip()); continue
        if s.startswith('#### '):
            out.append('#### ' + s[5:].strip()); continue
        out.append(s)
    txt = '\n'.join(out).strip() + '\n'
    return re.sub(r'\n{3,}', '\n\n', txt)


SRC.mkdir(exist_ok=True)
(SRC / 'qianyan.md').write_text(fix((D / 'preface.md').read_text()))
(SRC / 'daolun.md').write_text(fix((D / 'intro.md').read_text()))
(SRC / 'jieyu.md').write_text(fix((D / 'conclusion.md').read_text()))
(SRC / 'fulu1.md').write_text(fix((D / 'appendix.md').read_text()))
for i in range(1, 11):
    t = (D / ('ch%02d.md' % i)).read_text()
    body = fix(t, chapter=True)
    if i in PARTS:
        ttl, paras = PARTS[i]
        body = '## %s\n\n%s\n\n' % (ttl, '\n\n'.join(paras)) + body
    (SRC / ('ch%02d.md' % i)).write_text(body)
print('ok', sorted(p.name for p in SRC.iterdir()))
