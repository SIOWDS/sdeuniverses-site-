#!/usr/bin/env python3
"""第 577 号：把定稿 chapters/*.md 与读数装成 convert.py 认的 src/，并生成附录。只做装配，不动正文文字。"""
import glob, json, re
from pathlib import Path
Z = Path('/home/claude/zhuangzi'); C = Z / 'chapters'; R = Z / 'readings'; OUT = Path(__file__).parent / 'src'
OUT.mkdir(exist_ok=True)
for f in OUT.glob('*.md'): f.unlink()
one = lambda pat: next(iter(sorted(C.glob(pat))))
fix = lambda s: re.sub(r'^# 第 (\d+) 章　', r'# 第\1章　', s, count=1)
(OUT / 'qianyan.md').write_text(one('前言*').read_text())
(OUT / 'daolun.md').write_text(one('导论*').read_text())
(OUT / 'jieyu.md').write_text(one('结语*').read_text())
first = {1: '第一编', 5: '第二编', 12: '第三编', 27: '第四编', 38: '第五编', 43: '第六编'}
for i in range(1, 47):
    tx = fix(one('第%02d章*' % i).read_text()).strip()
    if i in first:
        h, _, b = one(first[i] + '_*').read_text().strip().partition('\n')
        tx = '#' + h.replace('# ', '# ', 1) + '\n\n' + b.strip() + '\n\n' + tx
    (OUT / ('ch%02d.md' % i)).write_text(tx + '\n')
order = ['逍遥游','齐物论','养生主','人间世','德充符','大宗师','应帝王','骈拇','马蹄','胠箧','在宥','天地','天道','天运','刻意','缮性','秋水','至乐','达生','山木','田子方','知北游','庚桑楚','徐无鬼','则阳','外物','寓言','让王','盗跖','说剑','渔父','列御寇','天下']
D = {}
for p in glob.glob(str(R / '第*.json')):
    d = json.load(open(p)); D[d['pian']] = d
def norm(t):
    for k in ('具体做法', '换看法', '混合', '拒答'):
        if k in str(t): return k
# 附录一
rows = ['| 章 | 篇 | 承重 | 可判错主张 | 求问场景 | 纯做法 | 混合 | 换看法 | 拒答 | 故事/单元 |', '|---|---|---|---|---|---|---|---|---|---|']
for i, k in enumerate(order):
    d = D[k]; sc = [norm(s['answer_type']) for s in d['R2_huicheng'].get('scenes', [])]
    r1 = d['R1_chengzhong']; r4 = d['R4_yangshi']
    rows.append('| %d | %s | %s | %d | %d | %d | %d | %d | %d | %s/%s |' % (i + 5, k, r1['supports'][:3], len(r1['claims']), len(sc), sc.count('具体做法'), sc.count('混合'), sc.count('换看法'), sc.count('拒答'), r4['units_story'], r4['units_total']))
fu1 = '''# 附录一　四个读数：规则、结果与逐篇记录

本书动笔前写下四个读数、预测和撤回条件。下面照实记录。这些数由同一底座的写手自己数，切分口径不完全统一，读数三由一人判定，只算自查，不算独立验证；用同一套规则数公认哲学文本的对照组没有跑。读者手里有原文，可以重数。

## 规则与结果

**读数一，承重比。** 每篇抽掉寓言和比喻，写下能拆出的可判错主张，问它们撑不撑得起本篇想让读者接受的结论。预测：内七多数篇撑不起。撤回线：内七过半撑得起，“不是哲学家”退到分层判。结果：33 篇共 227 条主张；撑得起 0 篇，部分 26 篇，撑不起 7 篇；内七部分 5 篇，撑不起 2 篇。撤回线未触及。“部分”占大多数，这是这个判断的软处，见第 42 章。

**读数二，回程率。** 只收“有人带着一个实际难处来问或来求教”的场景。“具体做法”指答复里有读者照着能做的下一步，“换看法”指让人换角度或放下，两者都有算“混合”，不答或骂走算“拒答”。预测：内篇低于三成。撤回线：过半，成对判词作废。结果见下表合计：全书 85 场，纯做法 5，混合 17，换看法 40，拒答 23，含做法 25.9%；内篇 19 场，含做法 31.6%，略超预测；外篇 16.7%；杂篇 37.5%。撤回线未触及。这条规则排除了好奇追问匠人的场景（痀偻承蜩、梓庆、吕梁丈夫、轮扁等，答的全是工序），对判词有利；算进去约三成，仍不到一半。

**读数三，翻转率。** 成语词典数据（chinese-xinhua）里首出处标为《庄子》的 448 条全部判定，不挑。预测：不低于四分之一。撤回线：低于一成。结果：一致 338，转义 72，相反 24，无法判断 14；翻转率 21.4%，未达预测；判定者认为普通读者熟悉的 113 条里 31.0%；内七篇 34.9%，外篇 18.7%，杂篇 12.7%。撤回线未触及。全表见附录三。

**读数四，样式谱。** 把每篇切成自然单元（一则故事或一段议论算一个），数故事单元占比。预测：内篇和外篇短章高，外篇论说低。结果：内篇 46/78，外篇 81/168，杂篇 62/136，全书 189/382。外篇分组：檄文 7/51，论说 22/47（其中《刻意》《缮性》0，《天运》9/10），短章 45/56；杂篇同人 21/25。短章高于内篇，预测错了一半，“门人把作品抄成论点”只能收窄到《刻意》《缮性》和檄文组。

判词因此改过：“一切怎么办”改为“到要紧处，多半”；“现实的账隐去了”改为“账他都写了，只是把不用算账判得更高，又举不出一个实例”；《人间世》改按最硬的例外来写。

## 逐篇记录

''' + '\n'.join(rows) + '\n\n“承重”一栏是判定者的判断：部分、撑不起；没有一篇判为撑得起。\n'
(OUT / 'fulu1.md').write_text(fu1)
# 附录二：说明书
ps = ['# 附录二　三十三张说明书', '', '正文各章末尾的说明书汇在这里，方便查。“说明书”是比方：作品不是药，没有标准剂量。抽掉这个比方，留下来的判据是这件事还能不能改。', '']
for i, k in enumerate(order):
    s = one('第%02d章*' % (i + 5)).read_text()
    m = re.search(r'^\*\*说明书\*\*\s*$', s, re.M)
    items = [x.strip() for x in s[m.end():].splitlines() if x.strip()]
    ps.append('## 第 %d 章　%s' % (i + 5, k)); ps.append('')
    ps += [x + '\n' for x in items]
(OUT / 'fulu2.md').write_text('\n'.join(ps))
# 附录三：成语
r3 = json.load(open(R / 'R3_成语翻转.json'))
r3 = r3 if isinstance(r3, list) else r3.get('items') or r3.get('entries')
esc = lambda s: str(s).replace('|', '／').replace('\n', ' ')
def clean(s):
    s = re.sub(r'^同\d+[，,：:]?', '', str(s)).strip()
    if not s or s in ('同上',) or re.fullmatch(r'同.{0,6}', s):
        return '同一句话的变体'
    return s

ty = lambda t: [x for x in r3 if x.get('type') == t]
fu3 = ['# 附录三　成语翻转表', '', '成语词典数据里首出处标为《庄子》的 448 条，一人判定，同一底座，只算自查。词典里同一句话的变体各算一条（如木鸡 4 条、死灰 7 条），不是独立样本；按引文去重后约 324 个片段，翻转率 19.8% 到 21.6%。“一致”的 338 条和“无法判断”的 14 条不列。', '', '## 意思相反（24 条）', '', '| 成语 | 出处 | 原文语境 | 今义 |', '|---|---|---|---|']
fu3 += ['| %s | %s | %s | %s |' % (esc(x['word']), esc(x.get('pian', '')), esc(clean(x.get('yuan', ''))), esc(clean(x.get('jin', '')))) for x in ty('相反')]
fu3 += ['', '## 意思移动（72 条）', '', '| 成语 | 出处 | 原文语境 | 今义 |', '|---|---|---|---|']
fu3 += ['| %s | %s | %s | %s |' % (esc(x['word']), esc(x.get('pian', '')), esc(clean(x.get('yuan', ''))), esc(clean(x.get('jin', '')))) for x in ty('转义')]
(OUT / 'fulu3.md').write_text('\n'.join(fu3) + '\n')
(OUT / 'fulu4.md').write_text(Path(__file__).parent.joinpath('fulu4.md').read_text())
(OUT / 'fulu5.md').write_text(Path(__file__).parent.joinpath('fulu5.md').read_text())
print('assembled', len(list(OUT.glob('*.md'))), len(ty('相反')), len(ty('转义')))
