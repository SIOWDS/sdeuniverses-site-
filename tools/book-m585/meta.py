"""《认识权力》工具链共用常量；书号与 ISBN 从站上现算并已预留。版式照第 220、302 号。"""
NO = 585
SLUG = 'understanding-power'
TITLE = '认识权力'
SUBTITLE = '普通人都能懂的书'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'Understanding Power: A Book for Everyone'
EPIGRAPH = '权力是众多因素联合析出的一种局面：一处不必动，别处替它动，替动的人，自己的创造、自由、幸福排不上日程。'
AUTHOR = '王德生、高鹏'
AUTHORS = ['王德生', '高鹏']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-609-0'
PRICE_USD = 25.0
PRICE = 'US$25.00'
V = '20261105m585'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m585-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定', tier_reason='通俗读物，主张层；人物为虚构，全书无实跑数据', source='据两位作者已发表的专著与论文重写；AI（Claude）协作成稿，三审', rights='作者署名出版', tier_judge='Claude', tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导读、四十八章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
