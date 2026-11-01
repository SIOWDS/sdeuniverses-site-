"""第 552 号《陶哲轩如何才能与大模型公司和解与合作呢？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 551 号改写；版式照第 220、302 号。"""
NO = 552
SLUG = 'tao-reconcile-llm'
TITLE = '陶哲轩如何才能与大模型公司和解与合作呢？'
SUBTITLE = '从统一性数学到同一性谱系数学'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = ('How Can Terence Tao Reconcile and Cooperate with the Large-Model Companies? '
            'From Unified Mathematics to Identity-Genealogy Mathematics')
EPIGRAPH = '和解不是谈判，是赛道变多。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'math'
ISBN = '979-8-90690-554-3'
PRICE_USD = 22.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102a'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m552-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——命题、判据、九格读数、承重预测与证伪条件、构想场景，第 9–12 章测量均为研究设计、无真跑数据；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')
AUTHORSHIP = '核心问题、SDE 框架与全书母题由王德生提出；正文由 AI（Claude）协作撰写，经分章质检与统稿；无独立学术评审，无用户试验。'


def body_han(here=None):
    """正文汉字数（前言、十四章、结语与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
