"""第 535 号《SDE思想入门：普通人都能懂的智慧》（王德生　阳涌　著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 532 号（tools/book-m532/）移植；版式照第 220、302 号。
标签裁定卡取自书号预留档 .publish/volume-reservations/535.json 的 tier 字段。"""
import json as _json
from pathlib import Path as _P

NO = 535
SLUG = 'sde-thought-intro'
TITLE = 'SDE思想入门'
SUBTITLE = '普通人都能懂的智慧'
FULL_TITLE = 'SDE思想入门：普通人都能懂的智慧'
TITLE_EN = 'An Introduction to SDE Thought: Wisdom for Everyone'
EPIGRAPH = '世界不是摆在那里等你去拿的，它在发生；你在其中，也正在发生；凡是正在发生的，都可以改。'
AUTHORS = ['王德生', '阳涌']
AUTHOR = '　'.join(AUTHORS)          # 署名一律「王德生　阳涌　著」
BYLINE = AUTHOR + '　著'
ADVISOR = ''                          # 本书无指导
CATEGORY = 'core'
ISBN = '979-8-90690-051-7'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261031a'
DATE = '2026-10-31'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261031-m535-unit-v1.0'
SRC = '/home/claude/sde-intro/chapters'
CATALOG_SRC = '/home/claude/sde-intro/catalog.json'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'

_RES = _P(__file__).resolve().parents[2] / '.publish' / 'volume-reservations' / ('%d.json' % NO)
TIER = _json.loads(_RES.read_text(encoding='utf-8'))['tier']


def stats():
    """convert.py 写下的字数统计（书稿正文汉字）；没有就返回 None。"""
    p = _P(__file__).parent / 'stats.json'
    return _json.loads(p.read_text()) if p.exists() else None
