#!/usr/bin/env python3
"""
书架与阅读器体检　check_bookshelf.py
用法：
    python3 tools/check_bookshelf.py            # 只做本地静态核查（秒级）
    python3 tools/check_bookshelf.py --online   # 加线上可达性（分钟级，要网）
    python3 tools/check_bookshelf.py --render   # 加渲染真跑（要 playwright）

为什么要有这个脚本：见 docs/bookshelf-maintenance.md「追记 · 2026-09-19」。
2026-09-19 查出 m/84、m/92 的翻页阅读器打得开、但一页也渲染不出——
它们在任何「链接可达性」检查里都是 200，坏的是 read.html 里那行 PDF_URL。
"""
import argparse, json, os, re, sys, glob, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, 'public')
SITE = 'https://sdeuniverses.com'
fails = []


def rel(p):
    return os.path.relpath(p, ROOT)


def local_of(url):
    """把站内 URL 映射到本地文件路径；站外返回 None"""
    if not url:
        return None
    if url.startswith(SITE):
        url = url[len(SITE):]
    url = url.split('#', 1)[0].split('?', 1)[0]  # 缓存参数（?v=…）不属于文件路径
    if not url.startswith('/'):
        return None
    p = os.path.join(PUB, urllib.parse.unquote(url).lstrip('/'))
    return p + 'index.html' if p.endswith('/') else p


def path_only(u):
    """去掉站点前缀、查询串与锚点，只留路径"""
    if u.startswith(SITE):
        u = u[len(SITE):]
    return u.split('#', 1)[0].split('?', 1)[0]


def is_r2_pdf(u):
    """Worker 从 R2 取的那一类：/students/**.pdf（与 src/worker.js 的拦截同口径，大小写不敏感）。
    必须先去掉 ?v= 缓存参数再判：2026-09-26 查出，#165、#195 的 pdfUrl 带 ?v=20260925，
    旧写法 u.endswith('.pdf') 因此不成立，两本 R2 上完好的 PDF 被 ① 反复误报为「本地文件不存在」。"""
    p = path_only(u)
    return p.startswith('/students/') and p.lower().endswith('.pdf')


def r2_code(u):
    """去线上真取前 1KB，返回 HTTP 码（桶里没有时 Worker 回落 ASSETS，得 404）"""
    import subprocess
    e = SITE + urllib.parse.quote(path_only(u), safe='/%')
    try:
        return subprocess.run(
            ['curl', '-s', '-o', os.devnull, '-w', '%{http_code}', '-r', '0-1023', e],
            capture_output=True, text=True, timeout=40).stdout
    except Exception:
        return 'ERR'


def check_catalog():
    """① catalog.json 与本地文件一致性；走 R2 的 PDF 不在本地，改为线上真取"""
    import concurrent.futures
    print('① catalog.json 与本地文件')
    cat = json.load(open(os.path.join(PUB, 'books/catalog.json'), encoding='utf-8'))
    items = cat['books']
    bad = 0
    r2 = []
    for it in items:
        for k in ('detailUrl', 'readUrl', 'chapterUrl', 'articlesUrl', 'pdfUrl', 'coverUrl'):
            u = it.get(k)
            p = local_of(u)
            if not p:
                continue
            # /students/**.pdf 走 R2，本地必然没有——但不能就此免检，留到下面去线上真取
            if is_r2_pdf(u):
                r2.append((it, k, u))
                continue
            if not os.path.exists(p):
                print(f'   ✗ #{it.get("number")} {it["title"][:16]} {k} → {u[-56:]}')
                bad += 1
    r2_bad = 0
    if r2 and not os.environ.get('SKIP_R2'):
        with concurrent.futures.ThreadPoolExecutor(8) as ex:
            codes = list(ex.map(lambda t: r2_code(t[2]), r2))
        for (it, k, u), code in zip(r2, codes):
            if code not in ('200', '206'):
                print(f'   ✗ #{it.get("number")} {it["title"][:16]} {k} R2 取不到（{code}）→ {u[-56:]}')
                r2_bad += 1
        note = f'（R2 上的 PDF {len(r2)} 个已线上真取，取不到 {r2_bad}）'
    else:
        note = f'（R2 上的 PDF {len(r2)} 个未查：SKIP_R2）' if r2 else ''
    print(f'   {len(items)} 条，缺失 {bad + r2_bad}{note}')
    if bad:
        fails.append(f'catalog 指向不存在的本地文件 {bad} 处')
    if r2_bad:
        fails.append(f'catalog 指向 R2 上取不到的 PDF {r2_bad} 处')



def check_vector_readers():
    """⑦ 翻页阅读器的矢量渲染：PDF 源阅读器必须走 SVGGraphics，且 getDocument 带 fontExtraProperties"""
    print('⑦ 翻页阅读器矢量渲染')
    allow = {'books/lion-city-glory/read.html'}  # 自有版式阅读器，单独维护
    bad = 0
    shared = open(os.path.join(PUB, 'books/reader/reader.js'), encoding='utf-8').read()
    if 'SVGGraphics' not in shared or 'fontExtraProperties' not in shared or 'isOffscreenCanvasSupported:false' not in shared or 'cMapUrl' not in shared:
        print('   ✗ books/reader/reader.js 缺矢量渲染或 fontExtraProperties'); bad += 1
    for r in sorted(glob.glob(os.path.join(PUB, 'books/**/read*.html'), recursive=True)):
        rp = os.path.relpath(r, PUB).replace(os.sep, '/')
        h = open(r, encoding='utf-8', errors='ignore').read()
        if 'reader-config' in h or 'getDocument' not in h or rp in allow:
            continue
        if 'SVGGraphics' not in h:
            print(f'   ✗ {rp} 仍是位图阅读器（用 tools/build_flip_reader.py migrate 迁移）'); bad += 1
        elif 'fontExtraProperties' not in h or 'isOffscreenCanvasSupported:false' not in h:
            print(f'   ✗ {rp} getDocument 缺 fontExtraProperties 或 isOffscreenCanvasSupported:false（矢量会静默退回位图）'); bad += 1
        elif 'cMapUrl' not in h:
            print(f'   ✗ {rp} getDocument 缺 cMapUrl/cMapPacked（用预置 CMap 的 CJK 字体会报 CMap baseUrl，该页退回位图或缺字）'); bad += 1
    print(f'   异常 {bad}')
    if bad:
        fails.append(f'翻页阅读器矢量渲染异常 {bad} 处')

def check_pdf_url():
    """③ 老阅读器的 PDF 源：存在性、中文未编码、指向已迁走的路径"""
    print('③ 老阅读器 PDF_URL')
    bad = raw = moved = 0
    for r in sorted(glob.glob(os.path.join(PUB, 'books/**/read.html'), recursive=True)):
        h = open(r, encoding='utf-8').read()
        if 'reader-config' in h:          # 新阅读器，走 ② 与 ④
            continue
        m = re.search(r'PDF_URL\s*=\s*(encodeURI\()?["\']([^"\']+)["\']', h)
        if not m:
            continue
        wrapped, u = bool(m.group(1)), m.group(2)
        if any(ord(c) > 127 for c in u) and not wrapped:
            print(f'   ! {rel(r)} 中文路径未 encodeURI：{u}')
            raw += 1
        if is_r2_pdf(u):
            # 走 R2，本地必然没有——但不能就此免检：
            # 2026-09-19 那次坏的正是「迁移后 read.html 没跟改」，
            # 本地查不出来，只能去线上真取一次。
            if os.environ.get('SKIP_R2'):
                continue
            code = r2_code(u)
            if code not in ('200', '206'):
                print(f'   ✗ {rel(r)} R2 取不到（{code}）：{u[:58]}')
                bad += 1
                moved += 1
            continue
        p = os.path.join(PUB, u.lstrip('/')) if u.startswith('/') \
            else os.path.join(os.path.dirname(r), u)
        if not os.path.exists(urllib.parse.unquote(p)):
            print(f'   ✗ {rel(r)} 指向不存在：{u[:60]}')
            bad += 1
            if '/students/' in u:
                moved += 1
    print(f'   缺失 {bad}（其中疑似迁移未跟改 {moved}）｜未编码 {raw}')
    if bad:
        fails.append(f'read.html 的 PDF_URL 断链 {bad} 处')
    if raw:
        fails.append(f'中文 PDF 路径未 encodeURI {raw} 处')


def check_covers():
    """书目页有封面文件却不引用"""
    print('② 书目页封面引用')
    lost = []
    for d in sorted(glob.glob(os.path.join(PUB, 'books/m/*/'))):
        idx = d + 'index.html'
        if not (os.path.exists(d + 'cover.jpg') and os.path.exists(idx)):
            continue
        if 'cover.jpg' not in open(idx, encoding='utf-8').read():
            lost.append(os.path.basename(d.rstrip('/')))
    print(f'   有封面文件却未引用：{lost or "无"}')
    if lost:
        fails.append(f'书目页丢封面 {len(lost)} 本：{lost}')


def check_abs_refs():
    """书架页的 CSS/JS 不应写死站点绝对地址（本地预览会拿线上文件）"""
    print('④ 书架静态资源引用')
    p = os.path.join(PUB, 'books/index.html')
    h = open(p, encoding='utf-8').read()
    hard = re.findall(r'(?:href|src)="(https://sdeuniverses\.com/books/[^"]+\.(?:css|js))"', h)
    print(f'   写死绝对地址：{hard or "无"}')
    if hard:
        fails.append(f'books/index.html 写死绝对地址 {len(hard)} 处')


def check_online():
    """② 线上可达性——必须带 -L，站内有大量 301/307"""
    import subprocess, concurrent.futures
    print('⑤ 线上可达性（跟随跳转）')
    cat = json.load(open(os.path.join(PUB, 'books/catalog.json'), encoding='utf-8'))

    def probe(args):
        u, rng = args
        if not u:
            return '—'
        e = urllib.parse.quote(u, safe=':/%?=&')
        a = ['curl', '-s', '-L', '-o', '/dev/null', '-w', '%{http_code}', e]
        if rng:
            a[1:1] = ['-r', '0-1023']
        try:
            return subprocess.run(a, capture_output=True, text=True, timeout=45).stdout
        except Exception:
            return 'ERR'

    def chk(it):
        ks = ['detailUrl', 'readUrl', 'chapterUrl', 'articlesUrl', 'pdfUrl', 'coverUrl']
        codes = [probe((it.get(k), k in ('pdfUrl', 'coverUrl'))) for k in ks]
        return it.get('number'), it['title'][:14], dict(zip(ks, codes))

    with concurrent.futures.ThreadPoolExecutor(12) as ex:
        rows = list(ex.map(chk, cat['books']))
    ok = {'200', '206', '—'}
    bad = [r for r in rows if not all(v in ok for v in r[2].values())]
    for n, t, d in bad:
        print(f'   ✗ #{n} {t} ' + ' '.join(f'{k}={v}' for k, v in d.items() if v not in ok))
    print(f'   {len(rows)} 条，异常 {len(bad)}')
    if bad:
        fails.append(f'线上异常 {len(bad)} 条')


def check_render(limit=None):
    """④ 渲染真跑——唯一能抓住 84/92 那类病的一道"""
    print('⑥ 阅读器渲染真跑')
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('   跳过：未装 playwright')
        return
    cat = json.load(open(os.path.join(PUB, 'books/catalog.json'), encoding='utf-8'))
    targets = [it for it in cat['books'] if it.get('readUrl') and it['readMode'] != 'info']
    if limit:
        targets = targets[:limit]
    bad = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        for it in targets:
            pg = b.new_page(viewport={'width': 1100, 'height': 800})
            try:
                pg.goto(it['readUrl'], wait_until='networkidle', timeout=60000)
                pg.wait_for_timeout(4000)
                body = pg.inner_text('body')
                cv = pg.evaluate(
                    "()=>{const c=document.querySelector('canvas');"
                    "return c && c.width>0 ? c.width+'x'+c.height : ''}")
                miss = ('载入失败' in body) or ('未能载入' in body)
                if miss or not cv:
                    print(f'   ✗ #{it.get("number")} {it["title"][:16]} '
                          f'{"载入失败" if miss else "无 canvas"}')
                    bad += 1
            except Exception as e:
                print(f'   ✗ #{it.get("number")} {it["title"][:16]} {type(e).__name__}')
                bad += 1
            finally:
                pg.close()
        b.close()
    print(f'   {len(targets)} 本，渲染失败 {bad}')
    if bad:
        fails.append(f'阅读器渲染失败 {bad} 本')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--online', action='store_true', help='加线上可达性')
    ap.add_argument('--render', action='store_true', help='加渲染真跑')
    ap.add_argument('--limit', type=int, help='渲染只跑前 N 本')
    a = ap.parse_args()

    check_catalog()
    check_covers()
    check_pdf_url()
    check_vector_readers()
    check_abs_refs()
    if a.online:
        check_online()
    if a.render:
        check_render(a.limit)

    print()
    if fails:
        print('体检不通过：')
        for f in fails:
            print('  ·', f)
        sys.exit(1)
    print('体检通过。')
