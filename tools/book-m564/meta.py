"""第 564 号《先有蛋还是先有鸡？》（王德生、阳涌 合著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 564 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算。"""
NO = 564
SLUG = 'egg-or-chicken'
TITLE = '先有蛋还是先有鸡？'
SUBTITLE = '源头是意义变化最快的那一维'
COVER_SMALL = '熊彼特 · 普里戈金 · 老子'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Egg or Chicken? The Source Is the Dimension Whose Meaning Changes Fastest'
EPIGRAPH = '比赛一直在跑，照片停在一个人手上。照片不假，假的是把照片当成比赛。'
AUTHOR = '王德生　阳涌'
AUTHORS = ['王德生', '阳涌']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-581-9'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103m564'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m564-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿三审后按出版令裁定',
            tier_reason='主张层为主——停差律、判死条款、三部名著的缝隙读法与三则前瞻预注册；不含真跑数据',
            cite_ok='true', context_layers='判据、结论',
            source='王德生、阳涌合著（母题、口径与承重命题由王德生给出并审定）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生、阳涌合著：全书母题、口径与承重命题由王德生给出并审定；正文由 AI（Claude）协作撰写，经统稿、联网事实核查与三审；无独立学术评审。'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
