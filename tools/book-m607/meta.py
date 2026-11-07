"""第 607 号《SDE思想大全：本体论·方法论·思想创新论》（王德生 著）排版常量。工具链承自第 605、606 号。
书号、ISBN、定价只在这里改。上站前须重新拉站上 catalog 复核 607 / 979-8-90690-639-7 未被占用。"""
NO = 607
SLUG = 'sde-compendium'
TITLE = 'SDE思想大全'
TITLE_SHORT = 'SDE思想大全'
SUBTITLE = '本体论·方法论·思想创新论'
COVER_SMALL = '本体论 · 方法论 · 思想创新论'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'The SDE Compendium: Ontology, Methodology and Thought Innovation'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
ISBN = '979-8-90690-639-7'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m607r2'
DATE = '2026-11-07'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']


CATEGORY = 'core'
UNIT_REV = '20261107-m607-unit-v1'
TIER = dict(tier='L0', tier_set_at='统稿',
            tier_reason='公开命题：本体论、方法论、思想创新论三部分整理自站上已公开的原典专著，属主张层与整理层，条件层不构成私密底本；沿用作者对自著专著先完整开放上站的做法，待作者确认',
            cite_ok='true', context_layers='判据、结论',
            source='王德生著；正文由 AI（Claude）协作统稿与审校，经初审、复审、思想审校与终审', rights='作者署名出版', tier_judge='Claude（依王德生上站令）',
            tier_date='2026-11-07')
AUTHORSHIP = '王德生著；正文由 AI（Claude）协作统稿与审校，经初审、复审、思想审校与终审；无独立学术评审。'
