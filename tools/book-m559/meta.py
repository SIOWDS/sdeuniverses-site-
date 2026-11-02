"""第 559 号《发生性回写律》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 556 号改写；版式照第 220、302 号。独著；书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/559.json；
557、558 号与 ISBN 565、566 已被其他书预留，顺延）。"""
NO = 559
SLUG = 'generative-writeback'
TITLE = '发生性回写律'
SUBTITLE = '为什么落叶不腐，森林会起火'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Law of Generative Write-back: Why Forests Burn When Leaves Do Not Rot'
EPIGRAPH = '回写不是搬回去，是再发生一次；不发生就堆积，堆积要么盖住，要么起火。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-567-3'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102b'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m559-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿三审后按出版令裁定',
            tier_reason='主张层为主——定律、判据、条件性论断、设想场景与可证伪清单；三个读数均未真跑；王德生出版令明示上站',
            cite_ok='true', context_layers='判据、结论',
            source='王德生著（母题与定律由王德生口述）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')
AUTHORSHIP = '王德生著：全书母题与定律由王德生口述提出；正文由 AI（Claude）协作撰写，经三审与统稿；无独立学术评审，无实测数据。'


def body_han(here=None):
    """正文汉字数（前言、导读、导论、四十章、结语、附录与后记），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
