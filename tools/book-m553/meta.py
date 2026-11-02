"""第 553 号《AI时代出版典范的革命》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 552 号改写；版式照第 220、302 号。"""
NO = 553
SLUG = 'publishing-paradigm-revolution'
TITLE = 'AI时代出版典范的革命'
SUBTITLE = '从公共平台到个人知识发生系统的转移'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = ('The Revolution in the Publishing Paradigm in the AI Era: '
            'From Public Platforms to Personal Knowledge-Genesis Systems')
EPIGRAPH = '出版：知识的发生，而不是发现。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-555-0'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102a'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m553-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——命题、判据、条件性论断、粗检验与作废条件、构想场景；不含真跑数据与未公开推演材料；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')
AUTHORSHIP = '核心命题与全书口径由王德生口述提出；正文由 AI（Claude）协作撰写，经三审与统稿；无独立学术评审，无用户试验。'


def body_han(here=None):
    """正文汉字数（前言、导论、二十四章、结语与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
