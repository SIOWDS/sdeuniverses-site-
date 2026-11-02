"""第 558 号《悬着才成事——秩序为什么要靠悬着活着》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 557 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/558.json）。"""
NO = 558
SLUG = 'suspension-makes-things-happen'
TITLE = '悬着才成事'
SUBTITLE = '秩序为什么要靠悬着活着'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Suspension Makes Things Happen: Why Order Lives on What Is Not Yet Settled'
EPIGRAPH = '走路之所以稳，是因为每一步都在倒。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-566-6'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102m558'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m558-unit-v1'
SRC = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（母题、判据、窗口判断、推翻条件、构想场景），无真跑数据；〔待核〕〔待验〕如实保留；王德生出版令：统稿、三审、印刷版、阅读友好版、封面、上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述母题＋九篇学员论文为材料＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')


def body_han(here=None):
    """正文汉字数（前言、导论、九章、结语、附录与后记），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
