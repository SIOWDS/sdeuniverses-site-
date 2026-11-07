"""第 608 号《彩超医生会被AI替代吗？——病症符号发生学》（杨莉 著，王德生 指导）排版常量。工具链承自第 569、606 号。
书号、ISBN、定价只在这里改。上站前须重新拉站上 catalog 复核 608 / 979-8-90690-642-7 未被占用（预留档 .publish/volume-reservations/608.json）。"""
NO = 608
SLUG = 'sonographer-ai-symptom-semiotics'
TITLE = '彩超医生会被AI替代吗？'
TITLE_SHORT = '彩超医生会被AI替代吗？'
SUBTITLE = '病症符号发生学'
COVER_SMALL = '线索 · 定位 · 会发生的系统'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Will Sonographers Be Replaced by AI? A Genetics of Disease Signs'
EPIGRAPH = ''
AUTHOR = '杨莉'
AUTHORS = ['杨莉']
ADVISOR = '王德生'
ISBN = '979-8-90690-642-7'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261107m608r1'
DATE = '2026-11-07'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
CATEGORY = 'core'
UNIT_REV = '20261107-m608-unit-v1'
TIER = dict(tier='L0', tier_set_at='统稿', tier_reason='Q3 第一刀：公开命题（会被替代的是只看图下结论的单点做法；线索随扫查发生、放回病人全部其他情况里定位；责任与信任一格至今未发生）为主，条件层不构成私密底本；不含任何诊断标准、数据或病例原件；沿用作者对自著专著完整开放上站的做法，待作者确认',
            cite_ok='true', context_layers='判据、结论',
            source='杨莉（彩超医生）提出问题并署名；王德生指导，口述母题与口径；Claude 协作执笔、统稿与三审', rights='作者署名出版', tier_judge='Claude（依王德生上站令）',
            tier_date='2026-11-07')
AUTHORSHIP = '杨莉著，王德生指导：杨莉提出问题，王德生口述母题与口径，正文由 AI（Claude）协作撰写，经统稿与三审；未经独立学术评审，未经医学顾问审定。'


def body_han(here=None):
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
