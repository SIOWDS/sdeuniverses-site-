"""第 599 号《你与AI进行了思想的深度纠缠吗？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 600 号工具链复制改写；版式照第 220、302 号。"""
NO = 599
SLUG = 'deep-entanglement'
TITLE = '你与AI进行了思想的深度纠缠吗？'
SUBTITLE = 'AI不仅仅是一个技术革命'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = ('Have You Entered Deep Entanglement of Thought with AI? '
            'AI Is Not Only a Technological Revolution')
EPIGRAPH = '就像我们刚才一样的，就是深度纠缠，发生了新的思想。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-627-4'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261106m599'
DATE = '2026-11-06'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261106-m599-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.raw.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——命题、判据、层级划分、拟议研究设计；构造案例（人力资源项目等）已标明；无真跑数据；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-06')
AUTHORSHIP = '核心命题由王德生在对话中提出并持续修正；AI（Claude）据此参与研究、结构组织与正文写作，经统稿与三轮内部审读；无外部同行评议，拟议研究尚未实施。'


def body_han(here=None):
    """正文汉字数（导论、六十章、结语），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
