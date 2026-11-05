"""第 579 号《接、不接与没接》（王德生、黄倩盈 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 578 号改写；版式照第 220、302 号。"""
NO = 579
SLUG = 'caught-let-go-never-reached'
TITLE = '接、不接与没接'
SUBTITLE = '一样东西凭什么稳得住'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Caught, Let Go, Never Reached: What Keeps a Thing Steady'
EPIGRAPH = '稳住的，都是挑着接的。放下的，会沉底。'
AUTHOR = '王德生　黄倩盈'
AUTHORS = ['王德生', '黄倩盈']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-601-4'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m579'
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m579-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（去处分法、沉底律、三家厚薄的读法）；两次查验用公开代码作代理，一回未支持，一回不决；三条判死条款未跑；写作与审校同一底座，无独立评审，未经真人内行审读；WDS博士出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生立题并定口径，王德生、黄倩盈署名，AI 协作成稿）', rights='作者署名出版', tier_judge='Claude（依 WDS博士出版令）',
            tier_date='2026-11-05')
BODY_CHARS = 202000   # 全书去空白字符数（含标点数字），由 make_web.py 核；展示“约 20 万字”
