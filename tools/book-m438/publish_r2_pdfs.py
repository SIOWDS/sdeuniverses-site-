#!/usr/bin/env python3
"""第 438 号署名更正：在 Actions 里由仓库源稿重排打印版／阅读版、改学习包，直接写 R2（PDF 不进 git）。
先核内容，三份都合格才上传；上传后逐份核 ETag＝MD5。结果写 m438-r2-result.json。"""
import hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
import boto3, pymupdf

HERE = Path(__file__).parent
OUT = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'm438'
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('AWS_REQUEST_CHECKSUM_CALCULATION', 'when_required')
os.environ.setdefault('AWS_RESPONSE_CHECKSUM_VALIDATION', 'when_required')
c = boto3.client('s3', endpoint_url='https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com', region_name='auto')
BUCKET = 'sdeuniverses-pdf'
SLUG = 'dialogue-semiogenesis'
KEYS = {'print': f'books/m/438/{SLUG}-print.pdf', 'reader': f'books/m/438/{SLUG}-reader.pdf',
        'learning': f'books/m/438/downloads/{SLUG}-learning-v1.0.pdf'}
OLD_LEARNING_MD5 = '29d56dd9e927f71983a9a62970e7f9d8'


def run(*a):
    subprocess.run(a, check=True, cwd=HERE)


for f in (HERE / 'tight-cache').glob('tight-*.json'):
    shutil.copy(f, '/tmp/' + f.name)
run(sys.executable, 'cover_pdf.py', '--src', 'cover-src', '--out', str(OUT))
run(sys.executable, 'build.py', '--fonts', '/usr/share/fonts/opentype/noto', '--out', str(OUT), '--only', 'print', '--only', 'reader')

old = OUT / 'learning.old.pdf'
c.download_file(BUCKET, KEYS['learning'], str(old))
assert hashlib.md5(old.read_bytes()).hexdigest() == OLD_LEARNING_MD5, 'learning pack in R2 is not the expected version'
run(sys.executable, 'patch_learning_pdf.py', str(old), 'cover-src/cover.png', str(OUT / 'learning.pdf'))

files = {'print': OUT / f'{SLUG}-print.pdf', 'reader': OUT / f'{SLUG}-reader.pdf', 'learning': OUT / 'learning.pdf'}
res = {}
for tag, path in files.items():
    d = pymupdf.open(path)
    pages = [p.get_text() for p in d]
    assert '胡志英' in d.metadata['author'], tag
    assert not any(re.search('王德生[　 ]著', t) for t in pages), tag
    if tag == 'learning':
        assert '原书作者：胡志英' in pages[0] and len(d) == 23
    else:
        assert '胡志英　著' in pages[2] and '著者' in pages[4] and '指导老师' in pages[4]
        assert '胡志英（John Hu）' in pages[5] and '本书由他指导' in pages[5], tag
        assert len(d) in (470, 550), (tag, len(d))
    raw = path.read_bytes()
    res[tag] = {'key': KEYS[tag], 'bytes': len(raw), 'md5': hashlib.md5(raw).hexdigest(), 'pages': len(d)}
for tag in ('print', 'reader'):
    res[tag]['offset'] = json.loads((OUT / f'toc-{tag}.json').read_text())['offset']
res['readerToc'] = json.loads((OUT / 'toc-reader.json').read_text())

for tag, path in files.items():
    r = res[tag]
    c.put_object(Bucket=BUCKET, Key=r['key'], Body=path.read_bytes(), ContentType='application/pdf', CacheControl='public, max-age=3600')
    h = c.head_object(Bucket=BUCKET, Key=r['key'])
    assert h['ContentLength'] == r['bytes'] and h['ETag'].strip('"') == r['md5'], tag
    print('R2 OK', tag, r['bytes'], r['md5'], r['pages'], r.get('offset'))
Path('m438-r2-result.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
