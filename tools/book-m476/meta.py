"""第 476 号《放不下：三界回写留下的洞》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 474 号改写；版式照第 220、302 号（build.py）。"""
NO = 476
SLUG = 'fangbuxia'
TITLE = '放不下'
SUBTITLE = '三界回写留下的洞'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'Letting Go: The Holes Left by Unfinished Write-back across the Three Realms'
VERDICT = '放不下，是三界中某一界的回写没有完成，留下一个随时会被激发的洞。'   # 全书判词（题词页、详情页、智能体都用这一句）
EPIGRAPH = VERDICT
AUTHOR = '王德生、鲍锦朝'
AUTHORS = ['王德生', '鲍锦朝']
ADVISOR = ''
CATEGORY = 'health'   # 健康与心理：本书谈放不下（无法释怀、上瘾与惯、执念），是自我／心理一类的题；站内同类《心在哪里？》（第 390 号）在此类（见 README）
ISBN = '979-8-90690-560-4'
PRICE_USD = 20.00      # 定价唯一来源：PDF 出版信息页、Word、详情页、catalog、/today/ 新书卡、学习包、预留档都从这里取（封底图上的定价印在 cover-back.jpg 里，改价须重出封底）
PRICE = 'US$%.2f' % PRICE_USD
V = '20261102b'
DATE = '2026-11-02'
EDITION = '2026年11月第1版'
EDITION_SP = '2026 年 11 月第 1 版'
UNIT_REV = '20261102-m476-unit-v1'
SRC = 'src/full.md'
COVER_DIR = '/home/claude/fangbuxia/out'   # 已定封面封底：cover-front.jpg、cover-back.jpg（1004×1418），不用 cover.py 重画
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='主张层为主——判词、三界回写的因果链、二十九条承重命题与三洞两清想通放下的分解；场景人家均为构想；不含真跑数据、调查或用户试验',
            cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生口述＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-11-02')
AUTHORSHIP = ('著者王德生、鲍锦朝；王德生口述二十九条承重命题并裁定口径；Claude 拟纲，执笔前言、附录一与后记，并统稿；'
              '导论、九章、结语与附录二至五由十位 Claude（Sonnet）执笔者并行写成，经一审、二审、三审；经王德生审定。无独立学术评审，无用户试验。场景人家为构想。')


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
