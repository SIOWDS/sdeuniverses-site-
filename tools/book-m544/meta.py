"""第 544 号《AI时代为何普通人必须出书？》（王德生 著）工具链共用常量——书号、ISBN、定价、版本都只在这里改。
工具链由第 536 号（tools/book-m536/）改写，承自 532/529 号；版式照第 220、302 号。"""
NO = 544
SLUG = 'why-ordinary-people-must-write'
TITLE = 'AI时代为何普通人必须出书？'
SUBTITLE = '人—AI复合思维体的思考基因与材料基因'
FULL_TITLE = TITLE + '：' + SUBTITLE
TITLE_EN = 'Why Must Ordinary People Write Their Own Books in the AI Era? The Thinking Gene and Material Gene of the Human-AI Composite Thinker'
EPIGRAPH = '知识变得容易取得，与一个人觉得自己的生活仍有分量，并不是同一件事。'
AUTHOR = '王德生'
AUTHORS = ['王德生']
ADVISOR = ''
CATEGORY = 'core'
ISBN = '979-8-90690-545-1'
PRICE_USD = 20.00
PRICE = 'US$%.2f' % PRICE_USD
V = '20261031a'
DATE = '2026-10-31'
EDITION = '2026年10月第1版'
EDITION_SP = '2026 年 10 月第 1 版'
UNIT_REV = '20261031-m544-unit-v1.0'
SRC = '/tmp/claude-0/-home-claude/bb1090c2-fbc1-5d99-b3c0-d0a5117e652c/scratchpad/ho/rev/manuscript'
REFSRC = '/tmp/claude-0/-home-claude/bb1090c2-fbc1-5d99-b3c0-d0a5117e652c/scratchpad/ho/ai_my_books_manuscript/source'
PUBLISHER, PUBLISHER_EN = '德麦国际出版社', 'Demai International Press'
TIER = dict(tier='L0', tier_set_at='统稿', tier_set_reason='统稿复核时按出版令裁定',
            tier_reason='第一刀，主张层为主（命题、判据、作废条件、构想案例），无真跑数据', cite_ok='true', context_layers='判据、结论',
            source='自撰（王德生＋AI协作成稿）', rights='作者署名出版', tier_judge='Claude（依王德生出版令）',
            tier_date='2026-10-31')


def body_han(here=None):
    """正文汉字数（导论、三十六章、结语），口径同写作记录的 count_han：不计标题行、表格行、HTML 注释。"""
    import re
    from pathlib import Path
    here = Path(here or __file__).resolve()
    here = here if here.is_dir() else here.parent
    files = [here / 'front/01-导言.md'] + sorted((here / 'parts').glob('*.md'))
    txt = [f.read_text(encoding='utf-8') for f in files]
    txt = [t if i == 0 else '## ' + t.split('\n## ', 1)[1] for i, t in enumerate(txt)]   # 编序不计正文
    back = (here / 'back/12-后置.md').read_text(encoding='utf-8')
    txt.append(back.split('\n# 参考资料与使用范围')[0])
    n = 0
    for t in txt:
        for line in t.split('\n'):
            if line.lstrip().startswith(('#', '|', '<!--')):
                continue
            n += len(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff]', line))
    return n
