"""第 565 号《何谓理性文明的根基？——不是一个统一的E》（王德生　胡志英 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 564 号改写；书号与 ISBN 从站里计算（2026-11-03 上站前已核无重号）。"""
NO = 565
SLUG = 'rational-civilization-ground'
TITLE = '何谓理性文明的根基？'
SUBTITLE = '不是一个统一的E'
COVER_SMALL = '牛顿 · 伽达默尔 · 韦伯'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'What Is the Ground of Rational Civilization? Not One Unified E'
EPIGRAPH = '三本书都把条件当成了一块现成的地；可是这块地是许多不一样的东西碰出来的，又一遍遍长硬了。'
AUTHOR = '王德生　胡志英'
AUTHORS = ['王德生', '胡志英']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-582-6'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103m565'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m565-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿三审后按出版令裁定',
            tier_reason='主张层为主——三本原著的缝隙读法、发生学判词、两次预登记运算与附录二的待验设想；含少量预登记运算，无真跑的独立数据',
            cite_ok='true', context_layers='判据、结论',
            source='王德生、胡志英合著（选题、口径与承重命题由王德生口述或裁定；三本原著由胡志英选定）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生、胡志英合著：胡志英选书，王德生立题、口述承重命题与裁定，正文由 AI（Claude）协作撰写，经统稿与四路三审；引文核对的是电子文本而非印刷本；无独立学术评审。'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
