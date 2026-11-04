"""第 572 号《K线人生——跃迁无法设计，只能接住》（段君毅　王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 571 号改写；版式照第 220、302 号。书号与 ISBN 从站里计算（预留档 .publish/volume-reservations/572.json）。"""
NO = 572
SLUG = 'k-line-life'
TITLE = 'K线人生'
SUBTITLE = '跃迁无法设计，只能接住'
FULL_TITLE = TITLE + '——' + SUBTITLE
TITLE_EN = 'K-Line Life: Leaps Cannot Be Designed, Only Caught'
EPIGRAPH = ('人生不是一张K线图，而是几条K线缠成的洪流：在名、链、数之中，由创造、自由、幸福三条意义K线推进，显露为真、善、美。'
            '意义三K轮流领头，只是1到N；旧结构死去，三维混沌碰撞，底子里的种子才可能涌现为一条新K线，那才是典范跃迁。'
            '跃迁无法设计，能设计的只是让碰撞发生，并且接得住它。')
AUTHOR = '段君毅　王德生'
AUTHORS = ['段君毅', '王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-591-8'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261104m572'
DATE = '2026-11-04'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261104-m572-unit-v1'
SRC = 'src/full.md'
MS_DIR = '/home/claude/klife/book'
CHARTS_DIR = '/home/claude/klife/run/charts'
# 书稿顺序：序言、二十七章、尾声、附录 A—D（附录AC.md 里含 A 与 C，assemble.py 拆开后按 A、B、C、D 排）
MS_FILES = ['00_序言.md'] + ['第%02d章.md' % i for i in range(1, 28)] + ['99_尾声.md', '附录AC.md', '附录B.md', '附录D.md']
# 八编：编名（按章号起点）与编首语（作编序），取自 /home/claude/klife/run/assemble.py
PARTS = {1: '第一编　一张图看不清人生', 4: '第二编　核心三角：显露、意义、信息', 8: '第三编　读一张缠图',
         11: '第四编　陡坡与轮换：1到N的两种运动', 14: '第五编　跃迁：0到1无法设计', 19: '第六编　能设计的只有土壤',
         22: '第七编　四种下跌与假跃迁', 25: '第八编　检验与边界'}
# 第 26 章的十张缠图（public/books/m/572/text/charts/<slug>.jpg）
CHARTS = [('任正非', 'renzhengfei'), ('乔布斯', 'jobs'), ('泰森', 'tyson'), ('高更', 'gauguin'), ('贾跃亭', 'jiayueting'),
          ('鲁迅', 'luxun'), ('罗琳', 'rowling'), ('褚时健', 'chushijian'), ('齐白石', 'qibaishi'), ('罗永浩', 'luoyonghao')]
CHART_URL = 'charts'   # 相对 text/index.html
REFSRC = ''
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='三审', tier_set_reason='三审后按出版令裁定',
            tier_reason='主张层为主（人生是几条K线缠成的洪流、陡坡与跃迁、三权收回、三维碰撞、种子三来源、四种下跌）；含十人回溯检验（预登记、部分判断已撤回，见第26章）；普通人案例均为构造；名人事实取自公开资料；二十路分章写作、统稿、三审',
            cite_ok='true', context_layers='判据、结论',
            source='合著（段君毅原书生发，段君毅、王德生著，AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依WDS博士令）',
            tier_date='2026-11-04')


def body_han(here=None):
    """正文汉字数（前言、八编编序与二十七章、尾声、附录），由 convert.py 写入 han.json。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())['body']
