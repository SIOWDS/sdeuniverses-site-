"""第 605 号《一个人怎么活得好》（王德生 著）排版常量。工具链承自第 604 号。
书号、ISBN、定价只在这里改。上站前须重新拉站上 catalog 复核 605 / 979-8-90690-637-3 未被占用。"""
NO = 605
SLUG = 'how-to-live-well'
TITLE = '一个人怎么活得好'
TITLE_SHORT = '一个人怎么活得好'
SUBTITLE = '三层成洪流，六条路起手，一天一年一生'
COVER_SMALL = '创造 · 自由 · 幸福'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'How Can One Person Live Well? Creation, Freedom and Happiness as One Flood'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
ISBN = '979-8-90690-637-3'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m605r1'
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
UNIT_REV = '20261107-m605-unit-v1'
TIER = dict(tier='L0', tier_set_at='统稿', tier_reason='公开命题：主张层（活得好＝三层首尾相衔成洪流、起手随真善美×三界而变、九格分谱、可推翻处）为主，条件层不构成私密底本；作者令上站',
            cite_ok='true', context_layers='判据、结论',
            source='王德生著（承重命题由王德生口述；全书经 20 位执笔者并行写成、独立质检与三审）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生上站令）',
            tier_date='2026-11-07')
AUTHORSHIP = '王德生著：承重命题由王德生口述，正文由 AI（Claude）协作撰写，经独立质检与三审；无独立学术评审。'
