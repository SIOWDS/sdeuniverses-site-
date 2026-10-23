"""第 453 号《爱在创造中成全》——全部书籍常量集中在此（build.py / cover.py / publish.py / assemble.py 都从这里取）。
ISBN 为暂定，上站前待作者确认：只改这里一处，再重跑 assemble/ cover / build / publish 即可。"""
NO = 453
SLUG = 'ai-zai-chuangzao-zhong-chengquan'
TITLE = '爱在创造中成全'
SUBTITLE = '把忍耐变成创造，把统一性升维为同一性谱系'
AUTHOR = '王德生'
ISBN = '979-8-90690-976-3'          # 暂定（待作者确认）
PRICE = 'US$23.00'
PRICE_USD = 23.0
EDITION = '2026年10月第1版'
VERSION = '20261023a'               # 资源版本号（?v=）
UNIT_REV = '20261023-m453-unit-v1'
PART_WORD = '部'
PUBLISHER = '德麦国际出版社'
PUBLISHER_EN = 'Demai International Press'
AGENT_NAME = '三问'                  # 智能体名（站内 catalog 未占用；本版尚未建智能体/学习包，publish 默认不挂入口）
TITLE_EN = 'Love Fulfilled in Creation'
NCHAP = 53
NPART = 7


_ROOT = None


def total_hanzi():
    import re
    from pathlib import Path
    root = Path(__file__).parent
    n = 0
    for f in ['front/00-前置.md', 'front/01-导论.md'] + sorted(str(p.relative_to(root)) for p in (root / 'parts').glob('*.md')) + ['back/09-结语.md', 'back/10-后置.md']:
        p = root / f
        if p.exists():
            n += len(re.findall(r'[一-鿿]', p.read_text(encoding='utf-8')))
    return n


def placeholders():
    return {'__ISBN__': ISBN, '__PRICE__': PRICE, '__SUBTITLE__': SUBTITLE, '__TITLE__': TITLE,
            '__WAN__': '%d' % round(total_hanzi() / 10000), '__NO__': str(NO), '__EDITION__': EDITION}
