"""第 570 号《卡夫卡并不荒诞——同一性谱系文学的第一个符号》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 560 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/570.json）。"""
NO = 570
SLUG = 'kafka-not-absurd'
TITLE = '卡夫卡并不荒诞'
SUBTITLE = '同一性谱系文学的第一个符号'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Kafka Is Not Absurd: The First Sign of Identity-Genealogy Literature'
EPIGRAPH = '卡夫卡并不荒诞。用统一性来理解同一性谱系，就是荒诞。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-589-5'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103m570'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m570-unit-v1'
SRC = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（两种自由、荒诞是读数、保守的现实主义、同一性的序列转换、残雪的定位），无真跑数据；作品一律转述；王德生令：二十个智能体并行写、统稿、三审、排版、三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述母题＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生令）',
            tier_date='2026-11-03')


def body_han(here=None):
    """正文汉字数（前言、导论、九章、结语、附录与后记），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
