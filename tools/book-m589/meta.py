"""第 589 号《千年难题，还要等下一个理论吗？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
书号 589：catalog 与预留档最大号 588，取下一号（与第 582—588 号同样顺延）。ISBN 979-8-90690-616-8：号段内 600—615 已用或已预留，取 616，校验位 8。定价 US$20 由 WDS博士 裁定。
工具链：data.py/pdf.py/cover.py/docx.js/web.py 为本书所写（版式照第 220、302 号，参数取自第 311 号 build.py）；build_unit、register、shelves、agent_page、gen_config、publish 由第 587 号改写。"""
NO = 589
SLUG = 'no-next-theory'
TITLE = '千年难题，还要等下一个理论吗？'
SUBTITLE = '以 SDE 为核心的人-AI 复合智能体怎样随时生成答案'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Millennial Questions: Must We Wait for the Next Theory? How an SDE-Centered Human-AI Composite Generates Answers on Demand'
EPIGRAPH = '不是一套理论系统的诞生，而是随时生成解决答案。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = None
CATEGORY = 'core'
LABEL = '哲学与SDE'
ISBN = '979-8-90690-616-8'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m589'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m589-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审定稿', tier_set_reason='三审定稿后按出版令裁定',
            tier_reason='母题、口径与三类病根由王德生给出；文字由 AI（Claude）多路协作成稿，经统稿与三审；全书现场均为设想与模拟，不作证据；三组对照未执行，判负条件全部未检验，没有独立学术评审。引用时只作本书的主张，不作证据；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='主张、判负条件（均未检验）',
            source='自撰（王德生著，AI 协作成稿、统稿与三审）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')
IRON_RULE = '不替当事人编造经历，不把书中设想的现场当作调查或证据，不判哪一派对，不替人作决定，不做诊断，不给医疗、法律、投资意见，不裁判教义，不评价现实制度与在任领导人'
BANS = ['不补造没说过的细节、日期或数据',
        '不判一个人的本性、身份或信仰是否正确，只陪他把这一格问清楚',
        '不用“发生”替已经造成的伤害开脱',
        '出现不想活、想伤害自己或别人等危险信号时，先停下一切整理，请他立刻联系专业人员和身边的人，紧急时拨打当地急救电话']
AUTHORSHIP = '王德生 著：母题、口径与三类病根由作者给出；文字由 AI（Claude）多路并行协作成稿，经统稿与三审；同一底座的执笔者与审稿者不能互作独立证据；全书现场均为设想与模拟，人物、对话和结果均为构造；三组对照未执行，判负条件全部未检验，没有独立学术评审'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
