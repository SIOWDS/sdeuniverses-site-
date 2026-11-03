"""第 571 号《医患复合体状态发生学——病不在病人身上，也不在医生眼里》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由上一号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/571.json）。"""
NO = 571
SLUG = 'doctor-patient-complex'
TITLE = '医患复合体状态发生学'
SUBTITLE = '病不在病人身上，也不在医生眼里'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The State Genesis of the Doctor–Patient Complex'
EPIGRAPH = '医学研究的不是人的病，而是医患复合体的状态发生；诊断不是发现的终点，而是状态发生的开端。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'health'
ISBN = '979-8-90690-590-1'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261103m571'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m571-unit-v1'
SRC = 'src/full.md'
MS_DIR = '/home/claude/yihuan'
MS_FILES = ['01-前言导读导论.md', '02-第1-2章.md', '03-第3-4章.md', '04-第5-6章.md', '05-第7-8章.md',
            '06-第9-10章.md', '07-第11-12章.md', '08-第13-14章.md', '09-第15-16章.md', '10-结语附录后记.md']
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（复合体生病、观察者仍是发现学、诊断是开端、状态发生学、三态与转换），无真跑数据、无临床试验；只谈理解，不给诊疗用药建议；人物均为虚构；王德生令：十个智能体分章写、统稿、三审、排版、三位一体上站', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述母题＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生令）',
            tier_date='2026-11-03')


def body_han(here=None):
    """正文汉字数（前言、导读、导论、四编编序与十六章、结语、附录与后记），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
