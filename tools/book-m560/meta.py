"""第 560 号《文学的同一性谱系——后现代之后，从卡夫卡到残雪》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 558 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/560.json）。"""
NO = 560
SLUG = 'literature-identity-genealogy'
TITLE = '文学的同一性谱系'
SUBTITLE = '后现代之后，从卡夫卡到残雪'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Identity Genealogy of Literature: After Postmodernism, from Kafka to Can Xue'
EPIGRAPH = '文学的后现代的救赎，应该是文学的同一性谱系。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-569-7'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102m560'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m560-unit-v1'
SRC = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（母题、谱系判断、作家定位），无真跑数据；作品一律转述；王德生令：并行写、加厚、统稿审校与三审、按第 220、302 号版式排版', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述母题＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生令）',
            tier_date='2026-11-02')


def body_han(here=None):
    """正文汉字数（前言、导论、九章、结语、附录与后记），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
