"""第 566 号《本末发生学——层级是怎样沉出来的》（王德生　陈晓艳 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 565 号改写；书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/566.json，2026-11-03 已核无重号）。"""
NO = 566
SLUG = 'benmo-genesis'
TITLE = '本末发生学'
SUBTITLE = '层级是怎样沉出来的'
COVER_SMALL = '黄帝内经 · 论语 · 涂尔干'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Genesis of Root and Branch: How Layers Settle Out'
EPIGRAPH = '本不是天生的，也不是圣人立下的，而是被那些号称「守本」的做法一天天做出来的。'
AUTHOR = '王德生　陈晓艳'
AUTHORS = ['王德生', '陈晓艳']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-583-3'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103m566'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m566-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿、联网事实核查与三审后按出版令裁定',
            tier_reason='主张层为主——三本原著的缝隙读法、本末律（层级发生律）与三条判死条款、第六编对已发表研究的转述；无真跑的独立数据',
            cite_ok='true', context_layers='判据、结论',
            source='王德生、陈晓艳合著（立题、轴与承重命题由王德生口述或裁定；三本原著由陈晓艳选定）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生、陈晓艳合著：陈晓艳选书，王德生立题、口述承重命题与裁定，正文由 AI（Claude）协作撰写，经统稿、联网事实核查、三审与段落合并；引文核对的是电子文本而非印刷本；无独立学术评审。'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
