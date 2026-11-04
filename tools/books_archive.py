#!/usr/bin/env python3
"""把专著 PDF 打成一个 zip 放进 R2 的 archive/，供一次性下载（见 src/archive-download.js）。
  build  <键哈希>   打包：books/ 与 students/wang-desheng/ 下的 PDF
  delete <键哈希>   删除这个压缩包
只接收网址密钥的 SHA-256，日志里不出现下载网址。"""
import concurrent.futures as cf, hashlib, os, re, sys, tempfile, zipfile
# 新版 botocore 默认打 CRC64 校验头，R2 不认（理由同 tools/pdf_offload.py）
os.environ.setdefault('AWS_REQUEST_CHECKSUM_CALCULATION', 'when_required')
os.environ.setdefault('AWS_RESPONSE_CHECKSUM_VALIDATION', 'when_required')
import boto3
from botocore.config import Config

BUCKET = 'sdeuniverses-pdf'
ENDPOINT = os.environ.get('R2_ENDPOINT', 'https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com')
PREFIXES = ('books/', 'students/wang-desheng/')
LEDGER = os.path.join(os.path.dirname(__file__), '..', 'ops', 'pdf-offload', 'ledger.tsv')


def client():
    return boto3.client('s3', endpoint_url=ENDPOINT, region_name='auto',
                        config=Config(signature_version='s3v4', retries={'max_attempts': 8, 'mode': 'standard'},
                                      max_pool_connections=16))


def list_pdfs(c):
    out = []
    for pre in PREFIXES:
        for page in c.get_paginator('list_objects_v2').paginate(Bucket=BUCKET, Prefix=pre):
            for o in page.get('Contents', []):
                if o['Key'].lower().endswith('.pdf'):
                    out.append((o['Key'], o['Size']))
    return out


def ledger_md5():
    res = {}
    if os.path.exists(LEDGER):
        for l in open(LEDGER, encoding='utf-8'):
            if l.strip() and not l.startswith('#'):
                p = l.rstrip('\n').split('\t')
                res[p[0]] = (int(p[1]), p[2])
    return res


def build(key_hash):
    c = client()
    items = list_pdfs(c)
    if not items:
        sys.exit('桶里没有找到 PDF')
    known = ledger_md5()
    total = sum(s for _, s in items)
    print(f'共 {len(items)} 份，{total / 2**30:.2f} GB')
    with tempfile.TemporaryDirectory() as td:
        zpath = os.path.join(td, 'a.zip')

        def fetch(it):
            k, size = it
            p = os.path.join(td, hashlib.sha1(k.encode()).hexdigest())
            c.download_file(BUCKET, k, p)
            got = os.path.getsize(p)
            if got != size:
                raise RuntimeError(f'字节数不对：{k} {got} != {size}')
            row = known.get(k)
            if row and row[0] == size:
                h = hashlib.md5()
                with open(p, 'rb') as f:
                    for b in iter(lambda: f.read(1 << 20), b''):
                        h.update(b)
                if h.hexdigest() != row[1]:
                    raise RuntimeError(f'MD5 不对：{k}')
            return k, p

        done = 0
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_STORED, allowZip64=True) as z, cf.ThreadPoolExecutor(8) as ex:
            batch = 64     # 分批，临时盘上不会同时压太多份
            for i in range(0, len(items), batch):
                for k, p in ex.map(fetch, items[i:i + batch]):
                    z.write(p, k)
                    os.remove(p)
                    done += 1
                print(f'  已打包 {done}/{len(items)}', flush=True)
        with zipfile.ZipFile(zpath) as z:
            names = z.namelist()
            if len(names) != len(items) or len(set(names)) != len(items):
                sys.exit('压缩包文件数不对')
            bad = z.testzip()
            if bad:
                sys.exit('压缩包校验失败：' + bad)
        key = f'archive/{key_hash}.zip'
        c.upload_file(zpath, BUCKET, key)
        up = c.head_object(Bucket=BUCKET, Key=key)['ContentLength']
        if up != os.path.getsize(zpath):
            sys.exit('上传后大小不对')
        print(f'压缩包已就绪：{len(names)} 份，{up / 2**30:.2f} GB')


def delete(key_hash):
    client().delete_object(Bucket=BUCKET, Key=f'archive/{key_hash}.zip')
    print('已删除')


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] not in ('build', 'delete') or not re.fullmatch(r'[0-9a-f]{64}', sys.argv[2]):
        sys.exit(__doc__)
    {'build': build, 'delete': delete}[sys.argv[1]](sys.argv[2])
