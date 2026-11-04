"""第 511 号《见面才放心吗？——科学需要未见面之信》（王德生 著）工具链共用常量。工具链由第 483 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/511.json）。"""
NO = 511
SLUG = 'jianmian-fangxin'
TITLE = '见面才放心吗？'
SUBTITLE = '科学需要未见面之信'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Must We Meet Before We Can Rest Easy? Science Needs Trust in the Unseen'
EPIGRAPH = '信就是所望之事的实底，是未见之事的确据。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'culture'
ISBN = '979-8-90690-979-4'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m511'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m511-unit-v1'
SRC = 'src/full.md'
MS_DIR = '/tmp/claude-0/-home-claude/55eee307-f238-59a7-9df5-c167b56a5a48/scratchpad/out/chapters'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿复核', tier_set_reason='统稿与全书复核后按出版令裁定',
            tier_reason='主张层为主（三种信、放心是信结的账、实验不是实践、李约瑟之问新答案、两条轴）；全书未做统计调查；构想人物已标明；学员情况只来自作者口述；引文与史实核验状态见附录二；二十路分章写作、统稿、全书复核，未经独立学术评审',
            cite_ok='true', context_layers='判据、结论',
            source='独著（王德生口述母题，AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生令）',
            tier_date='2026-11-04')


def body_han(here=None):
    """正文汉字数（前言、导读、七编编序与四十一章、结语、附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
