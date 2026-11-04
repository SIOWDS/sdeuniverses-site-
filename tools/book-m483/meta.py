"""第 483 号《AI时代还能守正创新吗？——从最安全的活法到最危险的生存》（王德生 著）工具链共用常量。工具链由第 572 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/483.json）。"""
NO = 483
SLUG = 'shouzheng-chuangxin'
TITLE = 'AI时代还能守正创新吗？'
SUBTITLE = '从最安全的活法到最危险的生存'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'Can We Still Hold the Line and Innovate in the Age of AI? From the Safest Way of Living to the Most Exposed'
EPIGRAPH = '从前是一边安全、一边危险；如今两边都危险，于是选择的依据，从“哪边安全”换成了“哪边值得”。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'ai'
ISBN = '979-8-90690-483-6'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m483'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m483-unit-v1'
SRC = 'src/full.md'
MS_DIR = '/home/claude/book/chapters'
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（门槛安全、两边都危险、回写抵达、三层核）；全书未做统计调查，追失灵与班级对照设计未执行；构造例子均已标明；引文与史实核验状态见附录三；二十路分章写作、统稿、三审',
            cite_ok='true', context_layers='判据、结论',
            source='独著（王德生口述母题，AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依WDS博士令）',
            tier_date='2026-11-04')


def body_han(here=None):
    """正文汉字数（前言、导言、五部部序与三十六章、部小结、结语、附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
