"""第 500 号《AI是加速你的落地——人-AI复合思考体的价值与意义》（王德生 著）工具链共用常量。
工具链由第 572 号、第 364 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/500.json）。"""
NO = 500
SLUG = 'jiasu-luodi'
TITLE = 'AI是加速你的落地'
SUBTITLE = '人-AI复合思考体的价值与意义'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'AI Speeds Up Your Landing, It Does Not Land for You: The Value and Meaning of the Human-AI Compound Thinker'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'ai'
ISBN = '979-8-90690-978-7'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m500'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m500-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（复合思考体、三本账、现实钟、一轮、竞争搬家）；外部研究多据公开来源核对，全书未做统计调查，作废条件未真跑，日常案例多为设想',
            cite_ok='true', context_layers='判据、结论',
            source='王德生立题并定母题，AI协作成稿', rights='作者署名出版', tier_judge='Claude（依WDS博士令）',
            tier_date='2026-11-04')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
