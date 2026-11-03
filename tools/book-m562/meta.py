"""第 562 号《缝隙创新法》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 561 号改写；版式照第 220、302 号。独著；书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/562.json）。"""
NO = 562
SLUG = 'gap-innovation-method'
TITLE = '缝隙创新法'
SUBTITLE = '从龙爪手到超级专著打造法'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Gap Innovation Method: From the Dragon Claw to the Super-Monograph Method'
EPIGRAPH = '「本来如此」的地方，就是缝。把一个「本来就有」，改写成「怎样发生的」。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-571-0'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103a'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m562-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿三审后按出版令裁定',
            tier_reason='方法层与主张层——缝隙＝发现学预设的定义、三大缝隙透视法、发生学解构工序与本方法的判死条款；不含真跑数据；按第 220、302 号版式排版',
            cite_ok='true', context_layers='判据、结论',
            source='王德生著（缝隙定义、三大透视与方法来路由王德生口述）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生著：缝隙的定义（发现学预设）、三大缝隙透视法与从龙爪手到超级专著打造法的方法来路由王德生口述提出；正文由 AI（Claude）协作撰写，经统稿、事实核查与三审；无独立学术评审，无实测数据。'


def body_han(here=None):
    """正文汉字数（前言、导论、二十七章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
