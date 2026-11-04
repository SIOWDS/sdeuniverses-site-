"""第 574 号《腐败与癌症——三律发生学视角下的同构病理学》（王德生 著）修订版工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 572、573 号改写；版式照第 220、302 号。卷号从站里计算（500 号以前无空号，照第 573 号接已发布最大号顺延；预留档 .publish/volume-reservations/574.json）；
ISBN 沿用本书已出版的 978-1-970820-36-2（2026 年 2 月首版，德麦国际出版社），不另配号。"""
NO = 574
NOLABEL = '德麦国际专著 · 第 574 号'
SLUG = 'corruption-and-cancer'
TITLE = '腐败与癌症'
SUBTITLE = '三律发生学视角下的同构病理学'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Corruption and Cancer: Isomorphic Pathology from the Perspective of Tri-Law Generative Theory'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'health'
ISBN = '978-1-970820-36-2'
PRICE_USD = 47.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m574'
DATE = '2026-11-04'
EDITION = '2026年2月第1版；2026年11月修订版'
EDITION_SP = '2026 年 2 月第 1 版；2026 年 11 月修订版'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
EPIGRAPH = '真正复制的不是人，不是细胞，而是模板。'
UNIT_REV = '20261104-m574-unit-v1'
MS_DIR = str(__import__('pathlib').Path(__file__).parent / 'src')
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='统稿与三审后按出版令裁定',
            tier_reason='医学哲学与治理哲学著作，主张层为主（意义三律与三模态；腐败＝价值→意义断路；模板复制与 Easy Copies；两关卡、三发散、27指纹、小我夺权；拆模板、修通路、建免疫）；未做临床或统计研究，书中点名引用的六种学术文献已核；2026年2月首版由王德生著；2026年11月修订版保持SIO原貌，统稿与三审由 AI（Claude）协作完成，未经独立学术评审；不构成诊疗建议',
            cite_ok='true', context_layers='判据、结论',
            source='专著（王德生著；原稿写作中有大模型协作；修订版统稿 AI 协作）', rights='作者署名出版', tier_judge='Claude（依WDS博士令）',
            tier_date='2026-11-04')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
