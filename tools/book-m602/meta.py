"""第 602 号《难得糊涂：原创力的人格根基》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 599 号工具链改来（599 承自第 600 号）；版式照第 220、302 号。"""
NO = 602
SLUG = 'nande-hutu'
TITLE = '难得糊涂'
SUBTITLE = '原创力的人格根基'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'Rare Muddle-Headedness: The Personality Roots of Originality'
EPIGRAPH = '糊涂，其实就是 SDE 洪流序列暂时不要进入秩序态，留在混沌态和介生态里面，这是一个"人格的熬制"。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-632-8'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m602'
DATE = '2026-11-07'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261107-m602-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
NPARTS, NCH = 10, 28
# 各编章号范围（含两端）
PART_RANGES = [(1, 3), (4, 4), (5, 6), (7, 9), (10, 12), (13, 15), (16, 18), (19, 21), (22, 23), (24, 28)]
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——命题、判据、日常构造场景；无真跑数据；附录 A 史实已逐条核来源；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-07')
AUTHORSHIP = '核心命题由王德生在对话中口述提出并持续修正；AI（Claude）据此统稿、组织多位执笔子代理成稿，经逐章质检与统稿复核；无外部同行评议。'


def body_han(here=None):
    """正文汉字数（前言、导论、二十八章、结语与附录 A），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
