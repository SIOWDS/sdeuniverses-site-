"""第 532 号《SDE 语感学：语言学的一个新典范》（胡志英 著，王德生 指导）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 529 号（tools/book-m529/）改写；版式照第 220、302 号。"""
NO = 532
SLUG = 'sde-language-sense'
TITLE = 'SDE 语感学'
SUBTITLE = '语言学的一个新典范'
FULL_TITLE = 'SDE 语感学：语言学的一个新典范'
TITLE_EN = 'SDE Language-Sense Studies: A New Paradigm for Linguistics'
EPIGRAPH = '语感不是一个人拥有的能力或知识，而是「句×场」的运行读数。'
AUTHOR = '胡志英'
AUTHORS = ['胡志英']
ADVISOR = '王德生'
CATEGORY = 'lang'
ISBN = '979-8-90690-532-1'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261031a'
DATE = '2026-10-31'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261031-m532-unit-v1.0'
SRC = '/home/claude/yugan/chapters'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
# 标签裁定卡（/home/claude/yugan/tier-card.md）
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='立题时未定标签，统稿复核',
            tier_reason='第一刀，主张层为主、无真跑数据', cite_ok='true', context_layers='判据、结论',
            source='合作（学员胡志英＋AI 协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-10-31')
