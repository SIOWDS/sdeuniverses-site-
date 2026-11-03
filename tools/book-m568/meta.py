"""第 568 号《先难受，后痛快——普通人都能明白的真正心理健康》（王德生、苏亚男 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 567 号改写；书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/568.json，2026-11-03 已核无重号、校验位 7）。"""
NO = 568
SLUG = 'hurt-then-release'
TITLE = '先难受，后痛快'
SUBTITLE = '普通人都能明白的真正心理健康'
COVER_SMALL = '张力 · 转换 · 释放'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Hurt First, Then Release: Real Mental Health for Everyone'
EPIGRAPH = '先难受，后痛快。心理健康不是没有张力的状态，也不是到了高处的超越，而是能一次次勇敢地进入混沌、进入纠缠、进入张力。'
AUTHORS = ['王德生', '苏亚男']
AUTHOR = '　'.join(AUTHORS)          # 署名「王德生　苏亚男 著」
AUTHOR_LIST = '、'.join(AUTHORS)
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-585-7'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103m568'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m568-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿、联网事实核查与三审后按出版令裁定',
            tier_reason='主张层为主——幸福律三拍（张力、转换、释放）与先结后解律的读法、对阿德勒《自卑与超越》与心流、PERMA、暴露疗法等近邻的转述、病的新分法与两条判死条款（未真跑）；无真跑的独立数据',
            cite_ok='true', context_layers='判据、结论',
            source='王德生、苏亚男著（立题、母题与承重命题由王德生口述或裁定）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生、苏亚男著：立题、母题与承重命题由王德生口述或裁定；正文由 AI（Claude）执笔与统稿，经联网事实核查与三审；阿德勒引文核对的是电子文本；无独立学术评审。'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
