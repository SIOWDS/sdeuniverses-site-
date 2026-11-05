"""《拿掉哪一样》工具链共用常量；书号与 ISBN 从站上现算并已预留。版式照第 220、302 号。"""
NO = 580
SLUG = 'take-one-away'
TITLE = '拿掉哪一样'
SUBTITLE = '普通人都能明白的“会了”'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Take One Away: What It Means to Know How'
EPIGRAPH = '会不会，要拿掉一样才知道；你的，是还改得动的那几处。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'edu'
ISBN = '979-8-90690-602-1'
PRICE_USD = 20.0
PRICE = 'US$20.00'
V = '20261105m580'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m580-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定', tier_reason='主张层为主；第9章一条身体数据，主要预测未通过', source='自撰（王德生立项＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude', tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导论、三十三章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
