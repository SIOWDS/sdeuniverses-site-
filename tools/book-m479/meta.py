"""第 479 号《生源减少以后，学校不能只会招生》（卫李娜 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 555 号改写；版式照第 220、302 号。「王德生指导」只写进前言，不上封面、书名页与书目。
卷号与 ISBN 由站内 catalog 计算空位取得（2026-11-02）：卷号 479 为当日站内 catalog 与书号预留档合并后、第 20 号之后的首个空号（468 已被预留）；ISBN 053 为 979-8-90690 号段最小空位。"""
NO = 479
SLUG = 'school-beyond-enrollment'
TITLE = '生源减少以后，学校不能只会招生'
SUBTITLE = '民办小学价值再生与可持续发展'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = ('After Enrollment Falls, a School Cannot Only Recruit: '
            'Value Regeneration and Sustainable Development of Private Primary Schools')
EPIGRAPH = '用父母心做教育，才能做出真教育。'
AUTHOR = '卫李娜'
AUTHORS = ['卫李娜']
ADVISOR = ''
CATEGORY = 'edu'
ISBN = '979-8-90690-053-1'
PRICE_USD = 23.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102a'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m479-unit-v1'
SRC = 'src/full.md'
RAW = 'src/full.md'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿与三审后按出版令裁定',
            tier_reason='主张层为主——管理学判断、诊断工具、条件性论断、设想场景与演示算例、命题登记与撤回条件；现场材料出自作者本人汇报与文章并逐字核对；不含实测回测数据；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='卫李娜著（王德生指导）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')
AUTHORSHIP = '卫李娜著，王德生指导：现场材料全部出自作者本人的工作汇报、课件、已发表文章与简历；正文由 AI（Claude）协作撰写，经统稿与三审；无独立学术评审，无实测回测数据。'


def body_han(here=None):
    """正文汉字数（前言、导读、导言、二十三章、结语与附录），由 convert479.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
