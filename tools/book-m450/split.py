#!/usr/bin/env python3
"""第 450 号：把单文件全稿（系列 Markdown 约定 + 本书【章旨】【题词】【编序】行首标记）切成 build.py 要的分卷稿。
用法：python3 split.py /path/全稿.md
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
PARTS = ['第一编', '第二编', '第三编', '第四编', '第五编', '第六编']
PUB = [
    ('书名', '《为什么人人都想重开？——游戏发生学》'),
    ('著者', '阳涌'),
    ('指导', '王德生'),
    ('执笔', '复合主体：王德生指导并裁定承重命题；阳涌著；文字在 AI 协作下成稿，统稿由 Claude 执笔'),
    ('出版', '德麦国际出版社（Demai International Press）· 新加坡'),
    ('编号', '德麦国际专著第 450 号'),
    ('ISBN', '979-8-90690-598-7'),
    ('定价', 'US$20.00'),
    ('开本', '170 mm × 240 mm'),
    ('字数', '__WAN__'),
    ('版次', '2026 年 10 月第 1 版'),
]
NOTES = [
    'AI 协作声明：本书由王德生指导，承重命题与各项裁定出自王德生，阳涌著；文字在 AI 协作下成稿，统稿与排版由 Claude 执笔。书中所有家庭、人物、机构与场景均为构想，不对应真实个案；所列数字、阈值与试验方案均为设计参数，不是经验结果。凡标〔待核〕处，出处尚未逐字核对原文。关于沉迷与健康的章节只作理解之用，不构成医疗、心理或教育建议，本书不替代医生或心理咨询的判断。',
    '全书结构：出版信息、作者介绍、题词、前言、导读、目录；六编三十八章；结语、附录 A—F（方法附录、全景缝隙表、致命条款登记表、术语对照、计算里的“重启”、参考书目）。',
    '版权所有　侵权必究',
]


def conv(lines):
    out = []
    for l in lines:
        if l.startswith('【章旨】'):
            out += ['> **章旨**', '> ' + l[4:].strip(), '']
        elif l.startswith('【编序】'):
            out += [l[4:].strip(), '']
        elif l == '@@PUBINFO':
            out += ['| 项 | 内容 |', '|---|---|'] + ['| %s | %s |' % kv for kv in PUB] + [''] + [n + '\n' for n in NOTES]
        else:
            out.append(l)
    return out


def main():
    src = Path(sys.argv[1]).read_text(encoding='utf-8')
    han = len(re.findall(r'[一-鿿]', src))
    src = src.replace('__WAN__', '约 %d 万字' % round(han / 10000))
    L = conv(src.split('\n'))
    L = [x.replace('__WAN__', '约 %d 万字' % round(han / 10000)) for x in L]
    tops, cur = [], ['__front__', []]
    tops.append(cur)
    for l in L:
        m = re.match(r'^# (.+)$', l)
        if m:
            cur = [m[1], []]; tops.append(cur)
        cur[1].append(l)
    front = tops[0][1]
    parts = [t for t in tops if t[0].startswith('第') and '编' in t[0][:4]]
    jie = [t for t in tops if t[0].startswith('结语')]
    back = [t for t in tops if t[0].startswith('附录')]
    assert len(parts) == 6 and len(jie) == 1 and len(back) == 1, (len(parts), len(jie), len(back))
    for d in ('front', 'parts', 'back'):
        (HERE / d).mkdir(exist_ok=True)
    (HERE / 'front/00-前置.md').write_text('\n'.join(front).strip() + '\n')
    for i, (t, ls) in enumerate(parts, 1):
        (HERE / ('parts/%02d-%s.md' % (i, PARTS[i - 1]))).write_text('\n'.join(ls).strip() + '\n')
    (HERE / 'back/09-结语.md').write_text('\n'.join(jie[0][1]).strip() + '\n')
    (HERE / 'back/10-后置.md').write_text('\n'.join(back[0][1]).strip() + '\n')
    print('split ok; han', han)


if __name__ == '__main__':
    main()
