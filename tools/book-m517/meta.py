"""第 517 号《思想寡头：AI时代的财富金字塔》（王德生 著）修订版工具链共用常量。
工具链由第 515 号改来；版式照第 220 号、章式照第 302 号。ISBN 沿用 2026 年 1 月纸本原号（作者提供），卷号见预留档。"""
NO = 517
SLUG = 'thought-oligarchs'
TITLE = '思想寡头'
SUBTITLE = 'AI时代的财富金字塔'
FULL_TITLE = '思想寡头：AI时代的财富金字塔'
TITLE_EN = 'Thought Oligarchs: Who Controls Wealth in the Age of AI'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'ai'
ISBN = '978-1-970820-11-9'
PRICE_USD = 55.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m517'
DATE = '2026-11-04'
EDITION = '2026年1月第1版 · 2026年11月修订上线版'
EDITION_SP = '2026 年 1 月第 1 版 · 2026 年 11 月修订上线版'
UNIT_REV = '20261104-m517-unit-v1'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（财富入口三次换底、思想寡头与发生中心两层、抄得走与抄不走、题库可编辑）；判断未经检验，书末附录写明怎样算错；具名案例取自公开资料，已联网核对；日常例子为设想；已出版纸本的修订版',
            cite_ok='true', context_layers='判据、结论',
            source='王德生原著（2026年1月第1版），依其裁定由AI协作修订', rights='作者署名出版', tier_judge='Claude（依WDS博士令）',
            tier_date='2026-11-04')


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
