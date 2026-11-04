"""第 576 号《AI来了，你往哪里躲？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 575 号改写；版式照第 220、302 号。"""
NO = 576
SLUG = 'where-to-hide'
TITLE = 'AI来了，你往哪里躲？'
SUBTITLE = '为何大部分人还没有危机感'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'AI Is Here. Where Will You Hide? Why Most People Still Feel No Crisis'
EPIGRAPH = '你必须和 AI 一起思考。竞争是复合体之间的竞争。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'ai'
ISBN = '979-8-90690-596-3'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m576'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m576-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（警报三件、两本账、复合体竞争、发生平台四判据）；外部研究多据公开介绍转述，全书未做调查或试验，撤回条件未真跑，人物场景为构想；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='王德生口述；AI（Claude）协作成稿', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-04')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
