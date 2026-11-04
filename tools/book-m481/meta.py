"""第 481 号《学科概念SDE发生学导论》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 571 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/481.json）。"""
NO = 481
SLUG = 'disciplinary-concept-genesis'
TITLE = '学科概念SDE发生学导论'
SUBTITLE = ''
FULL_TITLE = TITLE
TITLE_EN = 'An Introduction to the SDE Genesis of Disciplinary Concepts'
EPIGRAPH = '三维出新在场者，二维出新单位与新过程，一维出同类里的新成员；差别不在才智，在有几个位置在争；而在争的位置数，由上一次涌现留下的那一样东西决定。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-486-7'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m481'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m481-unit-v1'
SRC = 'src/full.md'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='判据与分布读数为主：五组真跑是书内对书内材料的检验，不是外部实测；单人编码，63 例改判无第三方复核；账目不合五十七条登记在附录十一；第 107 号书的材料不入合池计数；出版令：统稿、审校、三审、220/302 排版、三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生立题与裁定＋AI 协作成稿）', rights='作者署名出版', tier_judge='Claude（依出版令）',
            tier_date='2026-11-04')


def body_han(here=None):
    """全书汉字数（成书说明、凡例、导论、十编六十二章、结语、十一个附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
