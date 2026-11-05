"""《权力为何物》工具链共用常量；书号与 ISBN 从站上现算并已预留。版式照第 220、302 号。"""
NO = 581
SLUG = 'what-is-power'
TITLE = '权力为何物'
SUBTITLE = 'SDE权力发生学'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'What Is Power: The SDE Genesis of Power'
EPIGRAPH = '权力，是存在的 SDE 不对称性改变的发生。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-603-8'
PRICE_USD = 20.0
PRICE = 'US$20.00'
V = '20261105m581'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m581-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定', tier_reason='理论建构型专著，主张层；全书无实跑数据', source='著者两版书稿合并统稿（王德生立项；统稿由 AI 协作）', rights='作者署名出版', tier_judge='Claude', tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（序、导论、五十四章），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
