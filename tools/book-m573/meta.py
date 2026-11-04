"""第 573 号《从聪明到智慧——行动哲学的修炼之路》（王德生　王涛 著）工具链共用常量。工具链由第 511 号改写；版式照第 220、302 号。
卷号从站里计算（500 号以前无空号，照第 572 号接已发布最大号顺延；预留档 .publish/volume-reservations/573.json）；
ISBN 沿用本书已出版的 978-1-970820-06-5（2026 年 1 月首版，德麦国际出版社），不另配号。"""
NO = 573
SLUG = 'cong-congming-dao-zhihui'
TITLE = '从聪明到智慧'
SUBTITLE = '行动哲学的修炼之路'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'From Cleverness to Wisdom: The Practice of an Action Philosophy'
EPIGRAPH = '智慧不是更会算，而是更会发生；不是更会守规，而是更会生成规范。'
AUTHOR = '王德生　王涛'
AUTHORS = ['王德生', '王涛']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '978-1-970820-06-5'
PRICE_USD = 45.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m573'
DATE = '2026-11-04'
EDITION = '2026年11月增补版（首版2026年1月）'
EDITION_SP = '2026 年 1 月第 1 版；2026 年 11 月增补版'
UNIT_REV = '20261104-m573-unit-v1'
SRC = 'src/full.md'
MS_DIR = ''
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿与三审后按出版令裁定',
            tier_reason='行动哲学著作，主张层为主（聪明、智能、智慧三阶梯；发展、形式、发生三逻辑；两次跃迁；意义三律与价值三论；规范生成术）；全书未做统计调查，案例多为构造的示范；2026年1月首版由王德生、王涛著；2026年11月增补版的新增章节（第13章等）由 AI（Claude）协作执笔，经统稿与三审，未经独立学术评审',
            cite_ok='true', context_layers='判据、结论',
            source='合著（王德生、王涛著；增补部分 AI 协作成稿）', rights='作者署名出版', tier_judge='Claude（依WDS博士令）',
            tier_date='2026-11-04')


def body_han(here=None):
    """正文汉字数（专家推荐语、前言、怎样读这本书、导读、六编编序与二十一章、结语、附录、后记），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
