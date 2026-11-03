"""第 567 号《一颗心，一阵心，一片心——粒子心、波心、场心》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 566 号改写；书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/567.json，2026-11-03 已核无重号）。"""
NO = 567
SLUG = 'three-hearts'
TITLE = '一颗心，一阵心，一片心'
SUBTITLE = '粒子心、波心、场心'
COVER_SMALL = '詹姆斯 · 弗洛伊德 · 华生'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'One Heart, a Surge of Heart, a Field of Heart: Particle, Wave and Field'
EPIGRAPH = '心，是洪流的显露。它有三种状态——粒子心、波心、场心；健康的心，是三种心之间转得动。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-584-0'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103m567'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m567-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿、联网事实核查与三审后按出版令裁定',
            tier_reason='主张层为主——三部名著与四家之心的读法、三心转换律与五条判死条款（未真跑）、第七编对二十余家近邻的转述；无真跑的独立数据',
            cite_ok='true', context_layers='判据、结论',
            source='王德生著（立题、母题与承重命题由王德生口述或裁定）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生著：立题、母题与承重命题由王德生口述或裁定；正文由 AI（Claude）协作撰写，经统稿、联网事实核查与三审；引文核对的是电子文本；无独立学术评审。'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
