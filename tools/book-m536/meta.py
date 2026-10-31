"""第 536 号《AI时代普通人的知识发生机会》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 532 号（tools/book-m532/）改写；版式照第 220、302 号。"""
NO = 536
SLUG = 'ordinary-knowledge-genesis'
TITLE = 'AI时代普通人的知识发生机会'
SUBTITLE = '从农业与日常生活经验，到教育、健康、事业的知识母本与同一性谱系'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'Knowledge Genesis for Ordinary People in the AI Era: From Farm and Everyday Experience to Mother Texts in Education, Health and Work'
EPIGRAPH = '草长了一年，割过几次，又长起来，原本板结的土变得松软了。这一轮发生留下的变化，参与塑造下一轮发生的条件。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-536-9'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261031a'
DATE = '2026-10-31'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261031-m536-unit-v1.0'
SRC = '/home/claude/work/v11'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='立题时未定标签，统稿复核',
            tier_reason='第一刀，主张层为主（命题、判据、作废条件、构想案例），无真跑数据', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生＋AI 协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-10-31')
