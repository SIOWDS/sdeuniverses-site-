"""第 591 号《都做对了，怎么还没变》（孔凡鹤 著，王德生 指导）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 525 号改写；版式照第 220、302 号。
书号 591：500 以前无空号（唯一缺号 468 已预留），catalog、m/ 目录与预留档最大号 590，按第 587—590 号先例顺延。ISBN：号段 600—617 已用或已预留，全站未见 618，取 618，校验位 2。定价 US$22.00 由 WDS博士定。"""
NO = 591
SLUG = 'done-right-yet-unchanged'
TITLE = '都做对了，怎么还没变'
SUBTITLE = '心理治疗里被好意占住的那个位置'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Done Right, Yet Unchanged: The Position Occupied by Goodwill in Psychotherapy'
EPIGRAPH = '做得越对，越占住那个只有来访者能站的位置；改变在它空出时发生，却记不到任何人账上。'
AUTHOR = '孔凡鹤'
AUTHORS = ['孔凡鹤']
ADVISOR = '王德生'
CATEGORY = 'health'
ISBN = '979-8-90690-618-2'
PRICE_USD = 22.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m591'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m591-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审统稿后按出版令裁定',
            tier_reason='主张层为主（三把椅子、位置空出、记账）；全书三条判错条款与各章读数均未检验；案例一律为说明性合成案例，不作证据；第12章为外推与预测；写作与审校同一底座，无独立评审；WDS博士出版令明示排版上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（据孔凡鹤学员专栏九篇心理治疗论文熔铸（另有六篇的材料并入），由 AI 协作重写）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导读、导论、编首语、十二章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
