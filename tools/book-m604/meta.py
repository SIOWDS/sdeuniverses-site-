"""第 604 号《事实胜于雄辩：真的还是假的？》（王德生、张琼 著）排版常量。工具链承自第 569 号。
书号、ISBN、定价只在这里改。上站前须重新拉站上 catalog 复核 604 / 979-8-90690-636-6 未被占用。"""
NO = 604
SLUG = 'fact-vs-eloquence'
TITLE = '事实胜于雄辩：真的还是假的？'
TITLE_SHORT = '事实胜于雄辩'
SUBTITLE = '一句老话，三态纠缠，九格审判，五个领域'
COVER_SMALL = '混沌态 · 介生态 · 秩序态'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Do Facts Really Outweigh Eloquence? Fact as Three-State Entangled Occurrence'
AUTHOR = '王德生　张琼'
AUTHORS = ['王德生', '张琼']
ADVISOR = ''
ISBN = '979-8-90690-636-6'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m604'
DATE = '2026-11-07'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
CATEGORY = 'core'
UNIT_REV = '20261107-m604-unit-v1'
TIER = dict(tier='L0', tier_set_at='统稿', tier_reason='公开命题：主张层（事实＝三态纠缠发生、九格分谱、可证伪的小账）为主，条件层不构成私密底本；作者令上站',
            cite_ok='true', context_layers='判据、结论',
            source='王德生、张琼著（「事实」的定义与承重命题由王德生口述或裁定）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生上站令）',
            tier_date='2026-11-07')
AUTHORSHIP = '王德生、张琼著：「事实」的定义与承重命题由王德生口述或裁定，正文由 AI（Claude）协作撰写，经独立质检与统稿初审；复审与终审在上线后继续；无独立学术评审。'
