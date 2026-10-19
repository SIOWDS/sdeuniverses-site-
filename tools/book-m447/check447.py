import re, sys, subprocess, pypdf
from pathlib import Path
from PIL import Image, ImageDraw

D = Path('/home/claude/book447')
SKIP = re.compile(r'^(国家发生学导论|第 \d+ 章\s.*|导论|导读|目录|作者介绍|结语.*|参考书目|后记|\d+)$')
HEAD = re.compile(r'^([一二三四五六七八九十]+、.{1,24}|放回日子里|带 走 的 话|小 账)$')


def check(ed):
    pdf = D / f'国家发生学导论_第447号-{ed}.pdf'
    r = pypdf.PdfReader(str(pdf))
    n = len(r.pages)
    issues = []
    for i, p in enumerate(r.pages):
        t = p.extract_text() or ''
        lines = [l.strip() for l in t.split('\n') if l.strip()]
        body = [l for l in lines if not SKIP.match(l.replace('　', ' '))]
        if body and HEAD.match(body[-1]) and i + 1 < n:
            issues.append((i + 1, '页底落单标题', body[-1]))
    print(ed, 'pages', n, 'issues', issues)
    out = D / f'sheets-{ed}'
    out.mkdir(exist_ok=True)
    for f in out.glob('*'):
        f.unlink()
    subprocess.run(['pdftoppm', '-r', '28', '-png', str(pdf), str(out / 'p')], check=True)
    pages = sorted(out.glob('p-*.png'), key=lambda f: int(f.stem.split('-')[1]))
    per, cols = 24, 8
    for k in range(0, len(pages), per):
        ims = [Image.open(f) for f in pages[k:k + per]]
        w, h = ims[0].width, ims[0].height
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * (w + 6), rows * (h + 18)), (120, 120, 120))
        dr = ImageDraw.Draw(sheet)
        for j, im in enumerate(ims):
            x, y = (j % cols) * (w + 6), (j // cols) * (h + 18)
            sheet.paste(im, (x, y + 16))
            dr.text((x + 2, y + 2), str(k + j + 1), fill=(255, 255, 0))
        sheet.save(out / f'sheet-{k // per + 1:02d}.png')
    for f in pages:
        f.unlink()
    print('sheets', len(list(out.glob('sheet-*.png'))))


for ed in sys.argv[1:] or ['print', 'reader']:
    check(ed)
