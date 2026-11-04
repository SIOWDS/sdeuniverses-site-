"""第 487 号《真的能摸着石头过河吗？——马克思主义哲学复杂性发生学》（王德生 著）工具链共用常量。
工具链由第 572 号、第 364 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/487.json）。"""
NO = 487
SLUG = 'moshitou-guohe'
TITLE = '真的能摸着石头过河吗？'
SUBTITLE = '马克思主义哲学复杂性发生学'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Can We Really Cross the River by Feeling for the Stones? A Genesis of the Complexity of Marxist Philosophy'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-977-0'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m487'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m487-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（粥的统一性、外补、一个名额、石头三性、静态的同一性谱系）；判死条款与捞米清点未预注册、未真跑，多家原著未读，证据多为二手，已逐条标明',
            cite_ok='true', context_layers='判据、结论',
            source='王德生立题并定母题，AI协作成稿', rights='作者署名出版', tier_judge='Claude（依WDS博士令）',
            tier_date='2026-11-04')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
