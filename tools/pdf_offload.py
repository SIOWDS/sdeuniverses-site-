#!/usr/bin/env python3
"""PDF 迁出仓库（2026-10-02 起）：public/ 下的 PDF 进 R2 桶 sdeuniverses-pdf，仓库里删掉。

读者那一侧一个字都不用改：Worker 的 R2_OFFLOAD 段在「静态资源里没有这份 PDF」时
按同一路径问桶（见 src/worker.js 的 _r2PdfOnAssetMiss）。桶里的键＝public/ 之下的相对路径。

为什么要这件事：PDF 一份份提交进 git，仓库已到 3.1GB、16,974 个文件，
Cloudflare 静态资源上限是 2 万个文件、单个 25MiB——再出一两百本书就撞墙。

子命令
  plan                列出这一轮该迁的 PDF（不动任何东西）
  upload              传进桶并逐个核 MD5（要 R2 凭据：AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY）
  remove              把 upload 核过的那批从 git 删掉，登记进 ops/pdf-offload/ledger.tsv
  verify-live         按原网址逐个线上真取（带 Range，绕过边缘缓存），确认由 R2 供给且字节数对
  rehydrate           按台账把 PDF 从桶里取回 public/（搜索索引要抽 PDF 正文；要 R2 凭据）
  fetch <路径…>       不要凭据：从线上原网址把某几份 PDF 取回本地（本地工具要读 PDF 时用）

纪律
  · 只迁「24 小时内没人动过」的 PDF（--min-age-hours），给并行工作线留出验收时间；
  · 先进桶、核 MD5 相等，才许删；删完上线后逐个线上真取，有一份取不到就整笔 git revert；
  · 台账是唯一真相源：搜索索引、书架体检都按它判断「这份 PDF 在桶里」。
"""
import argparse, concurrent.futures as cf, hashlib, json, os, subprocess, sys, time, urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PUB = os.path.join(ROOT, 'public')
LEDGER = os.path.join(ROOT, 'ops', 'pdf-offload', 'ledger.tsv')
STATE = os.path.join(ROOT, 'ops', 'pdf-offload', '.verified.json')   # 本轮 upload 的结果，remove 只认它
BUCKET = 'sdeuniverses-pdf'
ENDPOINT = 'https://d3ea22f828ce19cf113a457ceba2c930.r2.cloudflarestorage.com'
SITE = 'https://sdeuniverses.com'
# 这些前缀在桶里另有用途（或由别的段供给），绝不碰
SKIP_PREFIX = ('students/', 'search/', 'plib/', 'live/', 'moments/')


def sh(*a, **k):
    return subprocess.run(a, cwd=ROOT, capture_output=True, text=True, **k)


def tracked_pdfs():
    out = sh('git', '-c', 'core.quotepath=off', 'ls-files', '-z', 'public').stdout
    res = []
    for p in out.split('\0'):
        if p.lower().endswith('.pdf') and p.startswith('public/'):
            k = p[len('public/'):]
            if not k.startswith(SKIP_PREFIX) and '..' not in k:
                res.append(k)
    return sorted(res)


def recently_touched(hours):
    """近 hours 小时内被提交碰过的 public/ 路径。
    浅克隆的边界提交会把整棵树都列成「新增」，不能算数——遇到它就停；
    若边界提交本身还在截止时间之内（历史不够深），宁可本轮一份都不迁。"""
    cutoff = time.time() - hours * 3600
    shallow = set()
    sp = os.path.join(ROOT, '.git', 'shallow')
    if os.path.exists(sp):
        shallow = {l.strip() for l in open(sp) if l.strip()}
    log = sh('git', '-c', 'core.quotepath=off', 'log', '--format=@%H %ct %s', '--name-only', 'HEAD').stdout
    touched, cur, own = set(), None, False
    for line in log.splitlines():
        if line.startswith('@'):
            sha, ts, subj = (line[1:].split(' ', 2) + [''])[:3]
            cur = int(ts)
            if cur < cutoff:
                break
            if sha in shallow:
                raise SystemExit(f'拉到的历史不够深：浅克隆边界 {sha[:8]} 还在 {hours} 小时之内，'
                                 '分不清哪些 PDF 最近动过。加大 fetch-depth 再跑。')
            # 迁移自己的提交（及其撤回）不算「有人动过」——否则撤回一次就得白等 24 小时
            own = subj.startswith('Offload ') or subj.startswith('Revert "Offload ')
        elif line.strip() and cur is not None and not own:
            touched.add(line.strip())
    return {p[len('public/'):] for p in touched if p.startswith('public/')}


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def s3():
    os.environ.setdefault('AWS_REQUEST_CHECKSUM_CALCULATION', 'when_required')
    os.environ.setdefault('AWS_RESPONSE_CHECKSUM_VALIDATION', 'when_required')
    import boto3
    from botocore.config import Config
    return boto3.client('s3', endpoint_url=ENDPOINT, region_name='auto',
                        config=Config(retries={'max_attempts': 6, 'mode': 'standard'},
                                      max_pool_connections=32))
    # 新版 botocore 默认给每次 PUT 打 CRC64 校验头，R2 不认会回 501——关掉它靠环境变量
    # AWS_REQUEST_CHECKSUM_CALCULATION=when_required（老版本不认这个 Config 参数，写进 Config 会直接报错）


def head(c, key):
    try:
        r = c.head_object(Bucket=BUCKET, Key=key)
        return r['ContentLength'], r['ETag'].strip('"')
    except Exception:
        return None, None


def candidates(a):
    allp = tracked_pdfs()
    recent = recently_touched(a.min_age_hours) if a.min_age_hours > 0 else set()
    pick = [k for k in allp if k not in recent]
    if a.only:
        import re
        rx = re.compile(a.only)
        pick = [k for k in pick if rx.search(k)]
    if a.limit:
        pick = pick[:a.limit]
    return allp, recent, pick


def cmd_plan(a):
    allp, recent, pick = candidates(a)
    size = sum(os.path.getsize(os.path.join(PUB, k)) for k in pick)
    print(f'仓库里的 PDF {len(allp)} 份；{a.min_age_hours} 小时内动过的 {len([k for k in allp if k in recent])} 份先不迁')
    print(f'本轮可迁 {len(pick)} 份，{size / 1e6:,.1f} MB')
    for k in pick[:20]:
        print('  ', k)
    if len(pick) > 20:
        print(f'   …… 另 {len(pick) - 20} 份')


def cmd_upload(a):
    _, _, pick = candidates(a)
    c = s3()

    def one(k):
        p = os.path.join(PUB, k)
        size, m = os.path.getsize(p), md5(p)
        with open(p, 'rb') as f:
            if f.read(4) != b'%PDF':
                return k, size, m, 'skip-not-pdf'
        s0, e0 = head(c, k)
        if s0 == size and e0 == m:
            return k, size, m, 'already'
        # put_object 是单段上传 ⇒ R2 的 ETag 就是 MD5，才能拿它逐字节核对（分段上传的 ETag 不是 MD5）
        with open(p, 'rb') as f:
            c.put_object(Bucket=BUCKET, Key=k, Body=f, ContentType='application/pdf',
                         CacheControl='public, max-age=3600')
        s1, e1 = head(c, k)
        return k, size, m, ('ok' if (s1 == size and e1 == m) else f'mismatch r2={s1}/{e1}')

    res, bad = [], []
    with cf.ThreadPoolExecutor(16) as ex:
        for i, r in enumerate(ex.map(one, pick), 1):
            (res if r[3] in ('ok', 'already') else bad).append(r)
            if i % 100 == 0:
                print(f'  … {i}/{len(pick)}')
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    json.dump([{'k': k, 'size': s, 'md5': m} for k, s, m, _ in res], open(STATE, 'w'), ensure_ascii=False)
    print(f'进桶并核过 MD5：{len(res)} 份（其中原本就在 {sum(1 for r in res if r[3] == "already")}）；不合格 {len(bad)}')
    for r in bad[:30]:
        print('  ✗', r[0], r[3])
    if bad and not a.allow_partial:
        sys.exit(1)


def cmd_remove(a):
    ver = json.load(open(STATE))
    if not ver:
        print('没有核过的 PDF，什么也不删'); return
    today = time.strftime('%Y-%m-%d', time.gmtime())
    have = set()
    if os.path.exists(LEDGER):
        have = {l.split('\t')[0] for l in open(LEDGER, encoding='utf-8') if l.strip() and not l.startswith('#')}
    rows, keys = [], []
    for v in ver:
        p = os.path.join(PUB, v['k'])
        # 核过之后文件又被人改了（并发提交）：这一份本轮不删
        if not os.path.exists(p) or os.path.getsize(p) != v['size'] or md5(p) != v['md5']:
            print('  跳过（核过之后本地变了）', v['k']); continue
        keys.append('public/' + v['k'])
        if v['k'] not in have:
            rows.append(f"{v['k']}\t{v['size']}\t{v['md5']}\t{today}\n")
    for i in range(0, len(keys), 200):
        r = sh('git', 'rm', '-q', '--', *keys[i:i + 200])
        if r.returncode:
            print(r.stderr); sys.exit(1)
    new = not os.path.exists(LEDGER)
    with open(LEDGER, 'a', encoding='utf-8') as f:
        if new:
            f.write('# path(相对 public/，即桶里的键)\tbytes\tmd5\toffloaded(UTC)\n')
        f.writelines(rows)
    print(f'已从 git 删除 {len(keys)} 份，台账新增 {len(rows)} 行 → {os.path.relpath(LEDGER, ROOT)}')


def ledger_rows():
    if not os.path.exists(LEDGER):
        return []
    out = []
    for l in open(LEDGER, encoding='utf-8'):
        if l.strip() and not l.startswith('#'):
            k, s, m, *_ = l.rstrip('\n').split('\t')
            out.append((k, int(s), m))
    return out


def live_probe(k, size):
    """跟随跳转（分站 PDF 会被 301 到 <名>.sdeuniverses.com），只认最后一跳的响应头。"""
    u = SITE + '/' + urllib.parse.quote(k, safe='/')
    r = subprocess.run(['curl', '-sL', '-o', os.devnull, '-D', '-', '-r', '0-1023', '-A', 'Mozilla/5.0 (pdf-offload)',
                        '--max-time', '60', u], capture_output=True, text=True)
    lines = r.stdout.replace('\r', '').split('\n')
    starts = [i for i, l in enumerate(lines) if l.lower().startswith('http/')]
    last = lines[starts[-1]:] if starts else []
    code = last[0].split()[1] if last and len(last[0].split()) > 1 else 'ERR'
    total, via = None, 'assets'
    for line in last:
        ll = line.lower()
        if ll.startswith('content-range:') and '/' in ll:
            total = ll.rsplit('/', 1)[1].strip()
        if ll.startswith('x-served-from:'):
            via = ll.split(':', 1)[1].strip()
    good = code == '206' and total == str(size)
    return k, code, total, via, good


def cmd_verify_live(a):
    """硬失败（404、5xx、字节数不对）＝读者打不开 → 退出码 1，工作流据此整笔撤回。
    「仍由静态资源出 200」＝边缘还压着删除前的旧副本：读者照样能读，只是还没轮到桶——
    隔一分钟复查一次，最多 --stale-wait 秒；到时仍是旧副本只报告、不撤回。"""
    rows = ledger_rows()
    if a.only_new:
        ver = {v['k'] for v in json.load(open(STATE))}
        rows = [r for r in rows if r[0] in ver]
    if a.sample:
        rows = rows[:a.sample]
    deadline = time.time() + a.wait
    while rows:
        k, code, total, via, good = live_probe(rows[0][0], rows[0][1])
        if good and via == 'r2':
            break
        if time.time() > deadline:
            print(f'等了 {a.wait}s 线上仍未由 R2 供给：{k} {code} {total} {via}')
            break
        time.sleep(15)

    def probe_all(rs):
        with cf.ThreadPoolExecutor(12) as ex:
            return list(ex.map(lambda r: live_probe(r[0], r[1]), rs))

    size = {r[0]: r[1] for r in rows}
    res = probe_all(rows)
    stale = lambda r: (not r[4]) and r[1] == '200' and r[3] == 'assets'
    t_end = time.time() + a.stale_wait
    while any(stale(r) for r in res) and time.time() < t_end:
        n = sum(1 for r in res if stale(r))
        print(f'  … {n} 份仍由静态资源旧副本供给（读者可读），60 秒后复查')
        time.sleep(60)
        again = {r[0]: r for r in probe_all([(r[0], size[r[0]]) for r in res if stale(r)])}
        res = [again.get(r[0], r) for r in res]
    hard = [r for r in res if not r[4] and not stale(r)]
    left = [r for r in res if stale(r)]
    vias = {}
    for r in res:
        vias[r[3]] = vias.get(r[3], 0) + 1
    print(f'线上真取 {len(res)} 份：由桶供给 {len(res) - len(hard) - len(left)}，'
          f'旧副本未过期 {len(left)}（可读），硬失败 {len(hard)}；供给来源 {vias}')
    for r in left[:20]:
        print('  ~', r)
    for r in hard[:40]:
        print('  ✗', r)
    if hard:
        sys.exit(1)


def cmd_rehydrate(a):
    rows = ledger_rows()
    c = s3()

    def one(r):
        k, size, m = r
        p = os.path.join(PUB, k)
        if os.path.exists(p) and os.path.getsize(p) == size:
            return 'have'
        os.makedirs(os.path.dirname(p), exist_ok=True)
        c.download_file(BUCKET, k, p)
        return 'ok' if os.path.getsize(p) == size else 'bad'

    with cf.ThreadPoolExecutor(16) as ex:
        res = list(ex.map(one, rows))
    print(f'按台账取回 {len(rows)} 份：新取 {res.count("ok")}，本地已有 {res.count("have")}，坏 {res.count("bad")}')
    if res.count('bad'):
        sys.exit(1)


def cmd_fetch(a):
    for k in a.paths:
        k = k.replace('public/', '', 1).lstrip('/')
        p = os.path.join(PUB, k)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        u = SITE + '/' + urllib.parse.quote(k, safe='/')
        r = subprocess.run(['curl', '-sfL', '-A', 'Mozilla/5.0 (pdf-offload)', '-o', p, u])
        print(('✓ ' if r.returncode == 0 else '✗ ') + k)
    print('取回的只是工作副本，用完删掉，不要再提交进 git（台账里的 PDF 由桶供给）。')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    for n in ('plan', 'upload'):
        s = sp.add_parser(n)
        s.add_argument('--min-age-hours', type=float, default=24)
        s.add_argument('--only', default='', help='只迁路径匹配这个正则的（试点用）')
        s.add_argument('--limit', type=int, default=0)
        if n == 'upload':
            s.add_argument('--allow-partial', action='store_true')
    sp.add_parser('remove')
    s = sp.add_parser('verify-live')
    s.add_argument('--only-new', action='store_true', help='只查本轮刚删的那批')
    s.add_argument('--sample', type=int, default=0)
    s.add_argument('--wait', type=int, default=600, help='等新部署生效的最长秒数')
    s.add_argument('--stale-wait', type=int, default=1200, help='旧副本最多再等多少秒')
    sp.add_parser('rehydrate')
    s = sp.add_parser('fetch')
    s.add_argument('paths', nargs='+')
    a = ap.parse_args()
    {'plan': cmd_plan, 'upload': cmd_upload, 'remove': cmd_remove, 'verify-live': cmd_verify_live,
     'rehydrate': cmd_rehydrate, 'fetch': cmd_fetch}[a.cmd](a)


if __name__ == '__main__':
    main()
