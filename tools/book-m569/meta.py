"""第 569 号《SDE思想创新法导论——从一本书出发，找到几本书，造一本书》（王德生 著）工具链常量——书号、ISBN、定价、版本只在这里改。
工具链承自第 566 号（220/302 版式）；书号与 ISBN 从站里计算（2026-11-03 已核：站内最大卷号 567、ISBN 中段最大 584，979-8-90690-587-1 无重号、校验位已核）。"""
NO = 569
SLUG = 'sde-innovation-methods'
TITLE = 'SDE思想创新法导论'
SUBTITLE = '从一本书出发，找到几本书，造一本书'
COVER_SMALL = '缝隙创新法 · 二阶碰撞法 · 九宫透镜法'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'An Introduction to SDE Methods of Thought Innovation: From One Book, Through Several, to a New One'
EPIGRAPH = '新思想不是被发现的，是发生的。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-587-1'
PRICE_USD = 25.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m569'
DATE = '2026-11-03'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261103-m569-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿、联网事实核查与三审后按出版令裁定',
            tier_reason='方法与工序为主——缝隙创新法、二阶碰撞法、九宫透镜法的工序、闸与工作卡；第四编六次试做是桌面模拟；判死条款未真跑，九宫落格未经第二人盲落；讲方法的专著不评创新智商',
            cite_ok='true', context_layers='工序、判据',
            source='王德生著（立题、三种创新法与承重命题由王德生口述或裁定）；AI 协作成稿', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-03')
AUTHORSHIP = '王德生著：王德生立题，口述缝隙创新法、二阶碰撞法、九宫透镜法与承重命题并裁定，正文由 AI（Claude）协作撰写，经统稿、联网事实核查、三审与段落合并；无独立学术评审。'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
