"""第 515 号《为何会想生孩子？》（王德生 著）工具链共用常量。
工具链由第 487 号改写；版式照第 220 号、章式照第 302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/515.json）。"""
NO = 515
SLUG = 'why-want-children'
TITLE = '为何会想生孩子？'
SUBTITLE = ''
FULL_TITLE = TITLE
TITLE_EN = 'Why Do We Come to Want Children?'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'culture'
ISBN = '979-8-90690-980-0'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m515'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m515-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（人口是接续、意义三流在三界上的权重组合、转界损耗、回写不对称）；四条律均为候选，只有律三用总和生育率作弱代理跑过一次预注册检验，未判负，不算证实；碰撞未做，母题先于配书；多家原著未读，证据多为转述，已逐条标明；日常案例多为设想',
            cite_ok='true', context_layers='判据、结论',
            source='王德生立题并定母题，AI协作成稿', rights='作者署名出版', tier_judge='Claude（依WDS博士令）',
            tier_date='2026-11-04')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
