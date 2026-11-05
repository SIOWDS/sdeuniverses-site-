"""第 592 号《耗在关系里的二十年，能不能变成收入？》（贝芳 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 586 号改写；版式照第 220、302 号。封面、封底不写指导者（站上口径），"在王德生老师指导下写成"见前言。"""
NO = 592
SLUG = 'twenty-years-in-between'
TITLE = '耗在关系里的二十年，能不能变成收入？'
SUBTITLE = '一位人力资源人走出内耗、建立人事管理慧店的路径'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Twenty Years Spent Caught in the Middle: Can They Become Income? An HR Practitioner’s Path Out of Attrition and Into a Knowledge Shop'
EPIGRAPH = '夹在中间的消耗，是三方碰撞压在一个大脑里结不了账；复合体结得了账，夹缝才长成三个市场。'
AUTHOR = '贝芳'
AUTHORS = ['贝芳']
ADVISOR = '王德生'
CATEGORY = 'business'
ISBN = '979-8-90690-619-9'
PRICE_USD = 22.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m592'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m592-unit-v1'
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审稿', tier_set_reason='三审稿后按出版令裁定',
            tier_reason='主张层为主（夹在中间的消耗是三方碰撞结不了账，复合体结得了账夹缝才长成三个市场）；作者亲历只取其本人已有文字与第 586 号所载，他人场景都标〔设想〕，慧店的产品、智能体、部落与交易都是设计、没有真实付费；站外著作只转述公认论点；写作与审校借助 AI 协作，无独立学术评审；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（贝芳著，王德生指导，AI 协作撰写与三审）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（前言、导论、六编编首语、二十九章与结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
