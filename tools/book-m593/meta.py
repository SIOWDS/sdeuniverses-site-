"""《抓不住的人》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 586、588 号改写；版式照第 220、302 号。书号与 ISBN 的取法与查重记录见 AVAILABILITY_NOTE 与预留档。
封面、封底不写指导者。本目录其余脚本不写死书号：换号只改 NO、V、UNIT_REV，再把目录改名为 book-m<NO>，跑 rebuild.sh。"""
NO = 593
SLUG = 'the-uncatchable'
TITLE = '抓不住的人'
SUBTITLE = '人力资源管理为何如此挑战'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The Uncatchable: Why Human Resource Management Is So Hard'
EPIGRAPH = '抓不住，所以不抓，推。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'business'
ISBN = '979-8-90690-621-2'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261105m%d' % NO
DATE = '2026-11-05'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261105-m%d-unit-v1' % NO
SRC = 'src/'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
SHELF_LABEL = '商业与管理'
AUTHORIZATION = '王德生署名，37万。按惯例是三审、排版、三位一体、上站。 定价：25'
AVAILABILITY_NOTE = ('出版令拟用第 468 号与 ISBN 979-8-90690-619-9，查重都不通过：468 号在预留档里已由《一看就不读》预留（第 590、591 号的预留档也都因此没有用它），'
                     '本号按第 587—592 号先例取顺延号 593；619 已是第 592 号的 ISBN，620 已是第 300 号的，取下一个空号 621，校验位 2。'
                     '《一看就不读》预留档所记的 ISBN 555-0 现为第 553 号所用，该预留是否作废待王德生裁定，本书没有动它。')
TIER = dict(tier='L0', tier_set_at='三审定稿', tier_set_reason='三审定稿后按出版令裁定',
            tier_reason='主张层为主，十条证伪均未直接检验，案例多为构造，写作与审校同一底座，无独立学术评审',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生著，AI 协作撰写与三审）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-05')


def body_han(here=None):
    """正文汉字数（写在前面、导论、十编编首语、六十章与结语），由 convert.py 写入 han.json。章末参考不计。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
