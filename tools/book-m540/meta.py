"""第 540 号《文明何以再生》工具链共用常量——书号、ISBN、定价、版本都只在这里改。"""
NO = 540
SLUG = 'civilization-regeneration'
TITLE = '文明何以再生'
TITLE_EN = 'How Civilizations Regenerate: The SDE Principle of Heterogeneous Write-Back and a Comparative History of China, the West and India'
SUBTITLE = 'SDE异质回写肥化原理与中西印文明比较史'
EPIGRAPH = '前一轮发生，给后一轮留下了什么？'
AUTHOR = '王德生　黄倩盈　胡志英'
AUTHORS = ['王德生', '黄倩盈', '胡志英']
ISBN = '979-8-90690-540-6'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261031a'
DATE = '2026-10-31'
EDITION = '2026年10月第1版'
UNIT_REV = '20261031-m540-unit-v1'
PKG = '/tmp/claude-0/-home-claude/9beef992-3be3-505a-b4d9-3ab916983aa9/scratchpad/pkg/sde_civilization_v08_three_authors'
SRC = PKG
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
VERDICT = '一个文明不是靠保存成果而再生，而是靠把异质的作用筛选、写回，使下一轮发生的条件变得更肥沃。'
CATEGORY = 'culture'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='王德生令全文公开', tier_reason='第一刀，主张层为主；无真跑数据；史料台账公开',
            cite_ok='true', context_layers='判据、结论', source='自撰（三位著者＋AI 协作成稿）',
            rights='作者署名出版；黄倩盈、胡志英署名经王德生确认', tier_judge='王德生裁定，Claude 记录', tier_date='2026-10-31')
