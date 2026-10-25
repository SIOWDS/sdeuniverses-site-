# 第408号全文网页 → 407 工具链分卷 Markdown
import re, sys, html
from bs4 import BeautifulSoup, NavigableString
from pathlib import Path
src = sys.argv[1]; out = Path(sys.argv[2])
soup = BeautifulSoup(open(src, encoding='utf-8').read(), 'html.parser')
wrap = soup.find('div', class_='wrap')

def inl(el):
    s = ''
    for c in el.children:
        if isinstance(c, NavigableString): s += str(c)
        elif c.name in ('strong', 'b'): s += '**' + inl(c) + '**'
        elif c.name == 'em': s += '*' + inl(c) + '*'
        elif c.name == 'br': s += '\n'
        else: s += inl(c)
    return s

def table(t):
    rows = []
    for tr in t.find_all('tr'):
        rows.append('| ' + ' | '.join(inl(c).replace('|', '｜').replace('\n', ' ').strip() for c in tr.find_all(['th', 'td'])) + ' |')
        if len(rows) == 1:
            rows.append('|' + '---|' * len(tr.find_all(['th', 'td'])))
    return '\n'.join(rows)

def blocks(nodes):
    o = []
    for n in nodes:
        if isinstance(n, NavigableString):
            if n.strip(): o.append(n.strip())
            continue
        c = n.get('class') or []
        if n.name == 'p' and 'takeaway' in c:
            n.find('span', class_='tk-l').decompose()
            t = inl(n).strip().lstrip('\n')
            o.append('> **带走的话**\n>\n' + '\n'.join('> ' + x for x in t.split('\n') if x.strip()))
        elif n.name == 'p':
            o.append(inl(n).strip())
        elif n.name == 'h2' and 'sec' in c:
            d = n.find('span', class_='dia')
            if d: d.decompose(); o.append('### ◆ ' + inl(n).strip())
            else: o.append('### ' + inl(n).strip())
        elif n.name == 'h3':
            o.append('### ' + inl(n).strip())
        elif n.name == 'blockquote':
            ps = [inl(p).strip() for p in n.find_all('p')]
            if ps and ps[0].startswith('这一章的问题：'):
                ps[0] = '**这一章的问题**：' + ps[0][len('这一章的问题：'):]
            o.append('\n'.join('> ' + p for p in ps))
        elif n.name == 'div' and 'ledger' in c:
            lab = n.find('span', class_='lt').get_text().strip()
            items = [inl(li).strip() for li in n.find_all('li')]
            o.append('> **%s**\n>\n' % lab + '\n'.join('> ' + x for x in items))
        elif n.name == 'div' and 'tw' in c:
            o.append(table(n.find('table')))
        elif n.name == 'table':
            o.append(table(n))
        elif n.name == 'ul':
            o.append('\n'.join('- ' + inl(li).strip() for li in n.find_all('li', recursive=False)))
        elif n.name == 'ol':
            st = int(n.get('start', 1))
            o.append('\n'.join('%d. %s' % (st + i, inl(li).strip()) for i, li in enumerate(n.find_all('li', recursive=False))))
        elif n.name == 'div' and ('rule' in c or 'bianxu' in c):
            pass
        else:
            raise SystemExit('unknown %s %s' % (n.name, c))
    return o

front, parts, back = [], [], []
cur = None
secs = [x for x in wrap.children if not isinstance(x, NavigableString)]
for el in secs:
    c = el.get('class') or []
    if el.name in ('nav', 'details') or 'hero' in c or 'foot' in c: continue
    if el.name == 'section' and ('front-sec' in c or 'back-sec' in c):
        t = el.find('h1', class_='front-title').get_text().strip()
        sub = el.find('div', class_='fs-sub', recursive=False)
        title = t + ('　' + sub.get_text().strip() if sub else '')
        body = [x for x in el.children if not (getattr(x, 'name', None) == 'h1' or (getattr(x, 'get', None) and 'fs-sub' in (x.get('class') or [])))]
        (front if 'front-sec' in c else back).append((title, blocks(body)))
    elif el.name == 'section' and 'part' in c:
        lab = el.find('div', class_='part-label').get_text().strip()
        pt = el.find(class_='part-title').get_text().strip()
        intro = blocks(list(el.find('div', class_='part-intro').children))
        cur = ['# %s　%s' % (lab, pt), '\n\n'.join(intro)]; parts.append(cur)
    elif el.name == 'div' and 'chapter' in c:
        cur.append('## %s　%s' % (el.find(class_='chap-label').get_text().strip(), el.find(class_='chap-title').get_text().strip()))
    else:
        cur.extend(blocks([el]))
(out / 'front').mkdir(parents=True, exist_ok=True); (out / 'parts').mkdir(exist_ok=True); (out / 'back').mkdir(exist_ok=True)
(out / 'front/00-前置.md').write_text('\n\n'.join('## %s\n\n%s' % (t, '\n\n'.join(b)) for t, b in front) + '\n')
for i, p in enumerate(parts, 1):
    (out / ('parts/%02d-%s.md' % (i, p[0][2:5]))).write_text('\n\n'.join(p) + '\n')
jy = [x for x in back if x[0].startswith('结语')][0]
(out / 'back/09-结语.md').write_text('# %s\n\n%s\n' % (jy[0], '\n\n'.join(jy[1])))
rest = [x for x in back if not x[0].startswith('结语')]
s = ''
apx = False
for t, b in rest:
    if t.startswith('附录'):
        if not apx: s += '# 附录\n\n'; apx = True
        s += '## %s\n\n%s\n\n' % (t, '\n\n'.join(b))
    else:
        s += '# %s\n\n%s\n\n' % (t, '\n\n'.join(b))
(out / 'back/10-后置.md').write_text(s)
print([t for t, _ in front], [p[0] for p in parts], [t for t, _ in back])
