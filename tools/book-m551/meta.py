"""第 551 号《AI时代的职业教育出路：技术的同一性谱系》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 549 号改写；版式照第 220、302 号。"""
NO = 551
SLUG = 'vocational-technical-identity-genealogy'
TITLE = 'AI时代的职业教育出路：技术的同一性谱系'
SUBTITLE = '基于SDE技术发生智能体的路径同一性发生学'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Way Out for Vocational Education in the AI Era: The Identity Genealogy of Technique, a Path-Identity Genesis Based on the SDE Technique-Genesis Agent'
EPIGRAPH = '药方是换尺子，不靠升格。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-553-6'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261101b'
DATE = '2026-11-01'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261101-m551-unit-v1'
SRC = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主（命题、六路径谱位读法、九格读数、十二条带失败标准的预言、构想场景），无真跑数据；王德生出版令明示三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-01')


def body_han(here=None):
    """正文汉字数（前言、导读、三十六章、结语与附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
