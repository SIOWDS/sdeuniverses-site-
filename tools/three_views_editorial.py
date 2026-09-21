#!/usr/bin/env python3
"""三视角专栏·编辑稿层。

生成器（three_views_quality_v2.py 等）按"逐字守恒"从原稿重排页面，结果是堆积式的：
一句一段、小标题粘在正文里、平台页眉混进首段。本工具建立一层**编辑稿**：

- 每篇一份 JSON 定稿单，存 tools/three_views_editorial/<id>.json，是唯一真源；
- 定稿单只用"句序号"引用原文，正文逐字取自原页面，改动必须在 fixes 里逐条申报；
- 构建时做两道账：①每一句要么被用、要么在 x 里写明丢弃理由；②成稿正文与原文
  （套用申报过的 fixes 之后）逐字相等。改不掉账就报错，不出页面。

页面被本工具改写后会带 data-editorial 标记，生成器见到这个标记就跳过（见各生成器
顶部的 editorial_locked()），所以 CI 重跑不会把编辑稿冲掉。

用法：
  python3 tools/three_views_editorial.py list read/a002     # 列出带序号的句子
  python3 tools/three_views_editorial.py build              # 构建全部定稿单
  python3 tools/three_views_editorial.py check              # 只跑两道账，不写文件
"""
from __future__ import annotations
import html
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

RELEASE = '20260921-editorial-v1'
ROOT = Path('public/three-views')
SPECS = Path('tools/three_views_editorial')
EXTRA_CSS = (
    '.prose .ed-lede{margin:0 0 26px;padding:16px 18px;border-left:3px solid var(--line);'
    'background:var(--soft);border-radius:0 7px 7px 0;line-height:1.95}'
    '.prose .ed-lede strong{display:block;margin-bottom:6px;font-size:13px;letter-spacing:.06em;color:var(--muted)}'
    '.prose blockquote.dlg{margin:14px 0;padding:10px 14px;border-left:3px solid var(--line);'
    'background:var(--soft);border-radius:0 6px 6px 0;color:var(--ink);line-height:1.9}'
    '.prose blockquote.dlg em{font-style:normal;color:var(--muted);font-size:12px;display:block;margin-bottom:3px}'
    '.prose .ed-foot{margin:34px 0 0;padding-top:20px;border-top:1px solid var(--line);'
    'font-size:13px;color:var(--muted);line-height:1.9}'
    '.prose .ed-merged{padding:18px;border:1px solid var(--line);border-radius:8px;background:var(--soft);line-height:1.95}'
    '.prose .ed-merged a{font-weight:600}'
    '.prose figure.figure{margin:22px 0}'
)
END_PUNCT = '。！？!?…'


# ---------------------------------------------------------------- 原文取句

def source_paragraphs(soup: BeautifulSoup) -> list[str]:
    """正文段落（不含原稿插图区与补录区）。"""
    prose = soup.select_one('.prose')
    out = []
    for el in prose.find_all(['p', 'blockquote'], recursive=False):
        if el.find_parent('section'):
            continue
        out.append(el.get_text())
    return out


def split_sentences(par: str) -> list[str]:
    """按句末标点切句；不跨段。"""
    sentences, buf = [], ''
    for i, ch in enumerate(par):
        buf += ch
        if ch in END_PUNCT:
            nxt = par[i + 1] if i + 1 < len(par) else ''
            if nxt in '”’"）)】』」':
                continue
            sentences.append(buf)
            buf = ''
    if buf.strip():
        sentences.append(buf)
    return sentences


def sentences_of(article_id: str) -> tuple[list[str], BeautifulSoup]:
    """句子取自冻结的原文快照；第一次构建时从当时的页面抽出并存档，之后只认快照。"""
    path = ROOT / article_id / 'index.html'
    soup = BeautifulSoup(path.read_text(encoding='utf8'), 'html.parser')
    frozen = SPECS / 'source' / (article_id.replace('/', '-') + '.txt')
    if frozen.exists():
        pars = [x for x in frozen.read_text(encoding='utf8').split('\n') if x.strip()]
    else:
        if soup.body.get('data-editorial'):
            raise AssertionError(f'{article_id}: 页面已是编辑稿，却没有原文快照——请从 git 历史取回原页面再冻结')
        pars = source_paragraphs(soup)
        frozen.parent.mkdir(parents=True, exist_ok=True)
        frozen.write_text('\n'.join(pars), encoding='utf8')
    out = []
    for par in pars:
        out.extend(split_sentences(par))
    return out, soup


def join(a: str, b: str) -> str:
    if not a:
        return b
    gap = ' ' if re.search(r'[A-Za-z0-9]$', a.rstrip()) and re.match(r'[A-Za-z0-9]', b.lstrip()) else ''
    return a.rstrip() + gap + b.lstrip()


def compact(s: str) -> str:
    return re.sub(r'\s+', '', s)


CJK = r'\u3400-\u9fff\u3000-\u303f\uff00-\uffef'
PUNCT_MAP = {',': '，', ':': '：', ';': '；', '!': '！', '?': '？', '(': '（', ')': '）'}


def normalize_punct(s: str) -> str:
    """半角标点贴着汉字时转全角；纯英文/数字处不动。申报 punct 的篇目两边同时套用。"""
    out = []
    for i, ch in enumerate(s):
        if ch in PUNCT_MAP:
            prev = next((c for c in reversed(s[:i]) if c != ' '), '')
            nxt = next((c for c in s[i + 1:] if c != ' '), '')
            if re.match(f'[{CJK}]', prev or '') or re.match(f'[{CJK}]', nxt or ''):
                out.append(PUNCT_MAP[ch])
                continue
        out.append(ch)
    text = ''.join(out)
    # 全角标点后面跟汉字时，去掉原稿里残留的空格
    return re.sub('([，。：；！？、）」』])\\s+(?=[' + CJK + '])', lambda mo: mo.group(1), text)


# ---------------------------------------------------------------- 装配

def assemble(spec: dict, sents: list[str]):
    """按定稿单装配，并跑两道账。返回 (blocks, audit_text, stats)。"""
    left = list(sents)
    used = [False] * len(sents)
    blocks, audit = [], []
    aid = spec['id']

    def take(i: int) -> str:
        if used[i]:
            raise AssertionError(f'{aid}: 第 {i} 句被用了两次')
        used[i] = True
        return left[i]

    for b in spec['blocks']:
        if 'h2' in b or ('cut' in b and 'from' in b):
            cut = b.get('cut', '')
            if cut:
                i = b['from']
                cur = left[i].lstrip()
                if not cur.startswith(cut):
                    raise AssertionError(f'{aid}: 第 {i} 句不以 {cut!r} 开头：{cur[:40]!r}')
                left[i] = cur[len(cut):]
                audit.append(cut)
            if 'h2' in b:
                blocks.append(('h2', b['h2']))
            elif not b.get('why'):
                raise AssertionError(f'{aid}: 切走的片段必须写理由')
        elif 'qcut' in b or 'pcut' in b:
            kind = 'q' if 'qcut' in b else 'p'
            cut = b.get('qcut') or b.get('pcut')
            head = ''
            for i in b.get('q', []):
                piece = take(i)
                audit.append(piece)
                head = join(head, piece)
            i = b['from']
            cur = left[i].lstrip()
            if not cur.startswith(cut):
                raise AssertionError(f'{aid}: 第 {i} 句不以 {cut!r} 开头：{cur[:40]!r}')
            left[i] = cur[len(cut):]
            audit.append(cut)
            blocks.append((kind, join(head, cut).strip(), b.get('who', '学员') if kind == 'q' else ''))
        elif 'psplit' in b:
            i = b['psplit']
            text = take(i)
            audit.append(text)
            rest = text
            pieces = []
            for mark in b['at']:
                k = rest.find(mark)
                if k <= 0:
                    raise AssertionError(f'{aid}: 第 {i} 句里找不到断点 {mark!r}')
                pieces.append(rest[:k])
                rest = rest[k:]
            pieces.append(rest)
            for piece in pieces:
                if piece.strip():
                    blocks.append(('p', piece.strip(), ''))
        elif 'p' in b or 'q' in b:
            key = 'p' if 'p' in b else 'q'
            text = ''
            for i in b[key]:
                piece = take(i)
                audit.append(piece)
                text = join(text, piece)
            if text.strip():
                blocks.append((key, text.strip(), b.get('who', '')))
        elif 'fig' in b:
            blocks.append(('fig', b['fig'], b.get('cap', '')))
        elif 'x' in b:
            for i in b['x']:
                audit.append(take(i))
            if not b.get('why'):
                raise AssertionError(f'{aid}: 丢弃必须写理由')
        elif 'note' in b:
            blocks.append(('note', b['note']))
        else:
            raise AssertionError(f'{aid}: 认不出的块 {b}')

    missing = [i for i, u in enumerate(used) if not u and left[i].strip()]
    if missing:
        raise AssertionError(f'{aid}: 这些句子既没用也没丢弃：{missing[:12]}')

    # 第二道账：成稿逐字等于原文（套用申报过的改动之后）
    src = ''.join(sents)
    got = ''.join(audit)
    for old, new in spec.get('fixes', []):
        if old not in src:
            raise AssertionError(f'{aid}: 申报的改动 {old!r} 在原文里找不到')
        src = src.replace(old, new)
        got = got.replace(old, new)
    if spec.get('punct'):
        src, got = normalize_punct(src), normalize_punct(got)
    if compact(src) != compact(got):
        a, b = compact(src), compact(got)
        k = next((n for n in range(min(len(a), len(b))) if a[n] != b[n]), min(len(a), len(b)))
        raise AssertionError(f'{aid}: 正文对不上账（第 {k} 字）原文…{a[max(0,k-30):k+30]!r} 成稿…{b[max(0,k-30):k+30]!r}')

    out = []
    for blk in blocks:
        if blk[0] in ('p', 'q'):
            text = blk[1]
            for old, new in spec.get('fixes', []):
                text = text.replace(old, new)
            if spec.get('punct'):
                text = normalize_punct(text)
            out.append((blk[0], text, blk[2]))
        else:
            out.append(blk)
    body_chars = sum(len(re.findall(r'[\u3400-\u9fff]', b[1])) for b in out if b[0] in ('p', 'q'))
    return out, {'body_chars': body_chars, 'sentences': len(sents),
                 'dropped': sum(len(b['x']) for b in spec['blocks'] if 'x' in b),
                 'fixes': len(spec.get('fixes', []))}


# ---------------------------------------------------------------- 渲染

def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def render_prose(blocks, spec) -> tuple[str, list[tuple[str, str]]]:
    parts, toc = [], []
    if spec.get('lede'):
        parts.append(f'<div class="ed-lede"><strong>编者导读</strong>{esc(spec["lede"])}</div>')
    for blk in blocks:
        if blk[0] == 'h2':
            anchor = f'sec-{len(toc) + 1}'
            toc.append((anchor, blk[1]))
            parts.append(f'<h2 id="{anchor}">{esc(blk[1])}</h2>')
        elif blk[0] == 'p':
            cls = ' class="list-item"' if re.match(r'^\d+[.．、]\s*', blk[1]) else ''
            parts.append(f'<p{cls}>{esc(blk[1])}</p>')
        elif blk[0] == 'q':
            label = blk[2]
            if label and blk[1].lstrip('（(').startswith(label.rstrip('（(')[:2]):
                label = ''
            who = f'<em>{esc(label)}</em>' if label else ''
            parts.append(f'<blockquote class="dlg">{who}{esc(blk[1])}</blockquote>')
        elif blk[0] == 'fig':
            src = blk[1]
            cap = blk[2]
            parts.append(
                f'<figure class="figure"><a href="{esc(src)}" rel="noopener" target="_blank">'
                f'<img alt="{esc(cap)}" decoding="async" loading="lazy" src="{esc(src)}"/></a>'
                f'<figcaption>{esc(cap)} · 点击放大</figcaption></figure>')
        elif blk[0] == 'note':
            parts.append(f'<p class="source-note">{esc(blk[1])}</p>')
    return '\n'.join(parts), toc


def minutes(chars: int) -> int:
    return max(1, round(chars / 480))


def rebuild_page(spec: dict) -> dict:
    aid = spec['id']
    sents, soup = sentences_of(aid)
    blocks, stats = assemble(spec, sents)
    prose_html, toc = render_prose(blocks, spec)

    url = f'/three-views/{aid}/'
    title = spec['title']
    lede = spec.get('lede', '')

    head = soup.head
    head.title.string = f'{title}｜三视角专栏'
    for sel, attr, val in [
        ('meta[name="description"]', 'content', (lede or '')[:150]),
        ('meta[property="og:title"]', 'content', title),
    ]:
        el = head.select_one(sel)
        if el:
            el[attr] = val
    ld = head.find('script', attrs={'type': 'application/ld+json'})
    if ld:
        data = json.loads(ld.string)
        data['headline'] = title
        if spec.get('byline'):
            data['author'] = {'@type': 'Person', 'name': spec['byline']}
        ld.string = json.dumps(data, ensure_ascii=False)
    if not head.find('style', id='ed-style'):
        st = soup.new_tag('style', id='ed-style')
        st.string = EXTRA_CSS
        head.append(st)

    soup.body['data-editorial'] = RELEASE

    hd = soup.select_one('header.article-head')
    hd.select_one('h1').string = title
    if spec.get('eyebrow'):
        hd.select_one('.eyebrow').string = spec['eyebrow']
    meta_bits = [spec.get('byline', ''), spec.get('source_note', ''),
                 f'正文约 {stats["body_chars"]:,} 字 · 约 {minutes(stats["body_chars"])} 分钟']
    hd.select_one('.meta').string = '　·　'.join(x for x in meta_bits if x)
    notice = hd.select_one('.notice')
    notice.string = spec.get('notice',
                             '本篇为编辑整理稿：分段、小标题、错字与标点经校订，观点与原话保持原貌；原稿可随时翻阅或下载核对。')
    toc_items = ''.join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in toc) or '<li><a href="#content">正文</a></li>'
    mob = hd.select_one('details.mobile-toc')
    mob.clear()
    mob.append(BeautifulSoup(f'<summary>本文目录</summary><ol>{toc_items}</ol>', 'html.parser'))

    prose = soup.select_one('.prose')
    keep_tail = [str(s) for s in prose.find_all('section', class_='archive-supplement')]
    foot = ('<div class="ed-foot">' + esc(spec.get('foot', '')) + '</div>') if spec.get('foot') else ''
    prose.clear()
    prose.append(BeautifulSoup(prose_html + ''.join(keep_tail) + foot, 'html.parser'))
    prose['data-editorial'] = RELEASE

    aside = soup.select_one('aside.toc')
    if aside:
        aside.clear()
        aside.append(BeautifulSoup(f'<strong>本文目录</strong><ol>{toc_items}</ol>', 'html.parser'))

    if spec.get('series'):
        nav = soup.select_one('nav.series-nav')
        links = []
        for kind, key in (('同类上一篇', 'prev'), ('同类下一篇', 'next')):
            item = spec['series'].get(key)
            if item:
                links.append(f'<a href="{esc(item["url"])}"><small>{kind}</small>{esc(item["title"])}</a>')
        if nav:
            nav.clear()
            nav.append(BeautifulSoup(''.join(links), 'html.parser'))

    (ROOT / aid / 'index.html').write_text(str(soup), encoding='utf8')
    return {'id': aid, 'url': url, 'title': title, 'chars': stats['body_chars'],
            'minutes': minutes(stats['body_chars']), 'excerpt': lede[:120], **stats}


def rebuild_merged(spec: dict) -> dict:
    """重复存档页：正文换成指路条，原稿入口保留。"""
    aid = spec['id']
    path = ROOT / aid / 'index.html'
    soup = BeautifulSoup(path.read_text(encoding='utf8'), 'html.parser')
    target = spec['merged_into']
    soup.body['data-editorial'] = RELEASE
    head = soup.head
    head.title.string = f'{spec["title"]}｜三视角专栏'
    canon = head.select_one('link[rel="canonical"]')
    if canon:
        canon['href'] = 'https://sdeuniverses.com' + target['url']
    if not head.find('style', id='ed-style'):
        st = soup.new_tag('style', id='ed-style')
        st.string = EXTRA_CSS
        head.append(st)
    hd = soup.select_one('header.article-head')
    hd.select_one('h1').string = spec['title']
    hd.select_one('.meta').string = spec.get('source_note', '本页为重复存档')
    hd.select_one('.notice').string = '本篇与下列文章是同一篇的另一份存档，已合并整理为一处阅读。'
    mob = hd.select_one('details.mobile-toc')
    if mob:
        mob.decompose()
    links = ''.join(f'<p><a href="{esc(t["url"])}">→ {esc(t["title"])}</a></p>' for t in [target] + spec.get('also', []))
    prose = soup.select_one('.prose')
    prose.clear()
    prose.append(BeautifulSoup(
        f'<div class="ed-merged"><p>{esc(spec["reason"])}</p>{links}'
        f'<p class="source-note">本页的原稿翻阅与 PDF 下载入口保留在上方，原件未作改动。</p></div>',
        'html.parser'))
    prose['data-editorial'] = RELEASE
    aside = soup.select_one('aside.toc')
    if aside:
        aside.decompose()
    nav = soup.select_one('nav.series-nav')
    if nav:
        nav.decompose()
    path.write_text(str(soup), encoding='utf8')
    return {'id': aid, 'url': f'/three-views/{aid}/', 'merged_into': target['url'], 'title': spec['title']}


# ---------------------------------------------------------------- 目录与清单

def update_catalog(edited: list[dict], merged: list[dict]):
    """清单、长文目录、分类文库、以及各页同类导航里的旧标题一起换掉。"""
    by_url = {e['url']: e for e in edited}
    gone = {m['url']: m for m in merged}

    man_path = ROOT / 'longform' / 'manifest.json'
    man = json.loads(man_path.read_text(encoding='utf8'))
    out = []
    for entry in man:
        if entry['url'] in gone:
            continue
        e = by_url.get(entry['url'])
        if e:
            entry['title'] = e['title']
            entry['chars'] = e['chars']
            entry['reading_minutes'] = e['minutes']
            entry['excerpt'] = e['excerpt']
            entry['editorial'] = RELEASE
        out.append(entry)
    man_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf8')

    old_titles = {}
    for p in sorted(ROOT.rglob('index.html')):
        text = original = p.read_text(encoding='utf8')
        in_catalog = '/longform/' in str(p) or '/library/' in str(p)
        for url, m in gone.items():
            # 只有目录与文库把重复存档整条撤下；图册等页面留着原链接，点进去看指路条
            if not in_catalog:
                continue
            text = re.sub(r'<li><a [^>]*href="%s"[^>]*>.*?</li>' % re.escape(url), '', text, flags=re.S)
            text = re.sub(r'<article class="card"(?:(?!</article>).)*?href="%s"(?:(?!</article>).)*?</article>' % re.escape(url),
                          '', text, flags=re.S)
        for url, e in by_url.items():
            def swap(mo, e=e, url=url):
                if mo.group(2).strip() and mo.group(2).strip() != e['title']:
                    old_titles.setdefault(url, mo.group(2).strip())
                return mo.group(1) + e['title'] + mo.group(3)
            text = re.sub(r'(<a [^>]*href="%s"[^>]*>(?:<small>[^<]*</small>)?)([^<]*)(</a>)' % re.escape(url), swap, text)
            text = re.sub(r'(href="%s"[^>]*>(?:<small>[^<]*</small>)?[^<]*</a><em>)[^<]*(</em>)' % re.escape(url),
                          lambda mo, e=e: f'{mo.group(1)}{e["chars"]:,} 字 · 网页长文{mo.group(2)}', text)
            text = re.sub(
                r'(<article class="card"(?:(?!</article>).)*?href="%s"[^>]*>[^<]*</a></h2><p>)(?:(?!</p>).)*?(</p><div class="small">)[^<]*(</div>)'
                % re.escape(url),
                lambda mo, e=e: f'{mo.group(1)}{html.escape(e["excerpt"])}{mo.group(2)}{e["chars"]:,} 字 · {e["minutes"]} 分钟{mo.group(3)}',
                text, flags=re.S)
        if text != original:
            p.write_text(text, encoding='utf8')
    return old_titles


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if mode == 'list':
        sents, _ = sentences_of(sys.argv[2])
        for i, s in enumerate(sents):
            print(f'{i:03d}\t{s}')
        return
    specs = [json.loads(p.read_text(encoding='utf8')) for p in sorted(SPECS.glob('*.json'))]
    edited, merged, report = [], [], []
    for spec in specs:
        if spec.get('merged_into'):
            merged.append(spec if mode == 'check' else rebuild_merged(spec))
            continue
        if mode == 'check':
            sents, _ = sentences_of(spec['id'])
            _, stats = assemble(spec, sents)
            report.append({'id': spec['id'], **stats})
        else:
            rec = rebuild_page(spec)
            edited.append(rec)
            report.append(rec)
    if mode == 'check':
        print(json.dumps(report, ensure_ascii=False, indent=1))
        print(f'两道账全过：{len(report)} 篇编辑稿，{len(merged)} 篇重复存档')
        return
    renamed = update_catalog(edited, merged)
    out = {'release': RELEASE, 'edited': edited, 'merged': merged, 'renamed_links': renamed}
    (ROOT / 'longform' / 'editorial-report.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding='utf8')
    print(f'编辑稿 {len(edited)} 篇，重复存档 {len(merged)} 篇，目录与同类导航已同步')


if __name__ == '__main__':
    main()
