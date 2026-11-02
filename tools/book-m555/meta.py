"""第 555 号《让经验长成思想》（阳涌 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 554 号改写；版式照第 220、302 号。「王德生指导」只写进前言，不上封面、书名页与书目。"""
NO = 555
SLUG = 'experience-grows-thought'
TITLE = '让经验长成思想'
SUBTITLE = '没被洗掉的差异'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = ('Letting Experience Grow into Thought: '
            'The Differences That Were Not Washed Away')
EPIGRAPH = '思想是经验的差异没有被清洗掉，而留下来的沉淀显露。'
AUTHOR = '阳涌'
AUTHORS = ['阳涌']
ADVISOR = ''
CATEGORY = 'edu'
ISBN = '979-8-90690-561-1'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102a'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m555-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——原理、判据、条件性论断、设想场景与构造算例、判决设计与撤回条件；不含真跑数据；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='阳涌著（核心命题由王德生口述）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')
AUTHORSHIP = '阳涌著：全书原理由王德生口述提出；正文由 AI（Claude）协作撰写，经三审与统稿；无独立学术评审，无实测数据。'


def body_han(here=None):
    """正文汉字数（前言、导论、十八章、结语与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
