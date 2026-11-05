"""第 584 号《不再有讲课的人》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 582 号改写；版式照第 220、302 号。"""
NO = 584
SLUG = 'no-more-lecturers'
TITLE = '不再有讲课的人'
SUBTITLE = '思想的发生与输出同时发生'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'No More Lecturers: Thought Happens as It Comes Out'
EPIGRAPH = '开口前已定稿或开口后没人被改的，让基底讲；人站到台上，是去押一个还没定的判断。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'edu'
ISBN = '979-8-90690-607-6'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m584'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m584-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审终审按出版令裁定',
            tier_reason='主张层为主；全书人物与课堂均为构造，五条失败条件尚无一条实跑，讲后差无实测数据',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（作者口述母题，由 AI 协作撰写）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（导论、编首语、二十四章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
