#!/usr/bin/env python3
"""第 438 号学习包：从迁桶前的原件重新改署名（小字库版）并写回 R2，核 ETag＝MD5。"""
import hashlib, os, subprocess, sys, urllib.request
from pathlib import Path
import boto3
HERE = Path(__file__).parent
OUT = Path(os.environ.get('RUNNER_TEMP', '/tmp'))
KEY = 'books/m/438/downloads/dialogue-semiogenesis-learning-v1.0.pdf'
URL = 'https://raw.githubusercontent.com/SIOWDS/sdeuniverses-site-/fc5f3b3f5cd4f0f66b543c841aec994f659e7cdd/public/' + KEY
raw = urllib.request.urlopen(URL, timeout=120).read()
assert hashlib.md5(raw).hexdigest() == '29d56dd9e927f71983a9a62970e7f9d8'
(OUT / 'old.pdf').write_bytes(raw)
subprocess.run([sys.executable, 'patch_learning_pdf.py', str(OUT / 'old.pdf'), 'cover-src/cover.png', str(OUT / 'new.pdf')], check=True, cwd=HERE)
new = (OUT / 'new.pdf').read_bytes()
assert len(new) < 2_000_000, len(new)
os.environ.setdefault('AWS_REQUEST_CHECKSUM_CALCULATION', 'when_required')
os.environ.setdefault('AWS_RESPONSE_CHECKSUM_VALIDATION', 'when_required')
c = boto3.client('s3', endpoint_url='https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com', region_name='auto')
c.put_object(Bucket='sdeuniverses-pdf', Key=KEY, Body=new, ContentType='application/pdf', CacheControl='public, max-age=3600')
m = hashlib.md5(new).hexdigest()
h = c.head_object(Bucket='sdeuniverses-pdf', Key=KEY)
assert h['ContentLength'] == len(new) and h['ETag'].strip('"') == m
print('R2 OK learning', len(new), m)
