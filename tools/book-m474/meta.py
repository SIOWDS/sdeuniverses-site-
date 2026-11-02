"""第 474 号《AI时代的焦虑：主体性如何重生》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 553 号改写；版式照第 220、302 号（build.py）。"""
NO = 474
SLUG = 'ai-era-anxiety'
TITLE = 'AI时代的焦虑'
SUBTITLE = '主体性如何重生'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'Anxiety in the AI Era: How Subjecthood Is Reborn'
VERDICT = '焦虑和问题的诞生，是用旧主体的问法去问新主体的处境。'   # 全书判词（题词页、详情页、智能体都用这一句）
EPIGRAPH = VERDICT
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'culture'   # 文明与社会：本书横跨家庭教育、职场、年轻人成长三处的社会性焦虑，不只是教育（见 README）
ISBN = '979-8-90690-557-4'
PRICE_USD = 50.00      # 定价唯一来源：PDF 出版信息页、Word、详情页、catalog、/today/ 新书卡、学习包、预留档都从这里取（封底图上的定价印在 cover-back.jpg 里，改价须重出封底）
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102a'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m474-unit-v1'
SRC = 'src/full.md'
COVER_DIR = '/home/claude/book474/out'   # 已定封面封底：cover-front.jpg、cover-back.jpg（1004×1418），不用 cover.py 重画
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——判词、因果链、承重命题、换主语的改问术与三组新问题；四十户人家的场景都是构想；不含真跑数据、调查或用户试验；王德生出版令明示三位一体上站',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')
AUTHORSHIP = ('判断、口径与十八条承重命题由王德生口述给出；Claude 拟纲，执笔前言、导读、导论、第 1 章、结语、附录一与后记，并统稿；'
              '其余三十九章与附录二至五由四十位 Claude（Sonnet）执笔者并行写成；经王德生审定。无独立学术评审，无用户试验。')


def counts(here=None):
    """convert.py 写入 han.json：body＝正文汉字（前言、导读、导论、四十章、结语、附录）；chars＝同一范围含标点的字数。"""
    import json
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    return json.loads((here / 'han.json').read_text())


def body_han(here=None):
    return counts(here)['body']


def wan(here=None):
    """对外“约 N 万字”：取统稿元数据 words（convert.py 写入 han.json 的 wan），与书内出版信息页一致。"""
    c = counts(here)
    return c.get('wan') or round(c['chars'] / 10000)
