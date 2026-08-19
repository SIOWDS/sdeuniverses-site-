#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotently publish the 纲领创新 entry points on the static homepage.

Content pages are committed separately. This script only patches navigation,
adds the homepage feature, and teaches the search-index builder the new section.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / 'public' / 'index.html'
SEARCH_BUILDER = ROOT / 'tools' / 'build_search_index.py'

NAV_MARK = '<!-- PROGRAMMATIC-INNOVATION-NAV -->'
FEATURE_MARK = '<!-- PROGRAMMATIC-INNOVATION-FEATURE -->'

NAV = f'''{NAV_MARK}
    <a href="/programmatic-innovation/" class="zh-only" style="color:#9B3F63;font-weight:800" title="以开辟研究对象、测量宪法与长期研究路径为标准的纲领性论文">纲领创新</a><a href="/programmatic-innovation/" class="en-only" style="color:#9B3F63;font-weight:800" title="Programmatic papers that open durable research spaces">Programmatic Innovation</a>
    '''

FEATURE = f'''{FEATURE_MARK}
<section id="programmatic-innovation-feature" style="padding:82px 22px;background:radial-gradient(circle at 16% 10%,rgba(123,96,210,.34),transparent 38%),radial-gradient(circle at 86% 18%,rgba(211,174,92,.18),transparent 33%),linear-gradient(142deg,#100c21,#21183e 58%,#151127);color:#f7f0e8;border-top:1px solid rgba(214,185,111,.25);border-bottom:1px solid rgba(214,185,111,.25)">
  <div style="max-width:1080px;margin:auto;display:grid;grid-template-columns:minmax(0,1.25fr) minmax(260px,.75fr);gap:34px;align-items:center">
    <div>
      <div style="font-size:12px;letter-spacing:.46em;color:#e2c873;margin-bottom:18px">新 栏 目 · 纲 领 创 新 · 开 辟 论 文</div>
      <h2 style="font-family:'Noto Serif SC',serif;font-size:clamp(42px,6.5vw,72px);line-height:1.12;margin:0 0 18px;letter-spacing:.06em">纲领创新</h2>
      <p style="font-size:18px;line-height:2;color:#d7cedf;margin:0 0 22px">不把一个新名称当作创新终点，而把它建设成一个别人可以进入、测量、反驳、修订并继续生长的研究空间。</p>
      <div style="font-size:12px;letter-spacing:.25em;color:#d6b865;margin-bottom:10px">开辟论文 · 王德生</div>
      <h3 style="font-size:clamp(27px,3.2vw,40px);line-height:1.4;margin:0 0 14px;color:#fff8e9">发生保真：互动系统如何在全部指标改善时失去生成能力</h3>
      <p style="font-size:15.5px;line-height:1.95;color:#c9bfd4;margin:0 0 24px">形成门、接续门与结算门的一般理论，四张账的测量宪法，账内不可辨识定理、发生债务与十年研究路线图。三万字纲领性增订版。</p>
      <div style="display:flex;gap:12px;flex-wrap:wrap"><a href="/programmatic-innovation/occurrence-fidelity/" style="display:inline-block;padding:12px 22px;background:#d7bd72;color:#171126;text-decoration:none;font-weight:800;border-radius:28px">阅读开辟论文 →</a><a href="/programmatic-innovation/" style="display:inline-block;padding:11px 21px;border:1px solid rgba(226,200,115,.55);color:#f0d98e;text-decoration:none;font-weight:700;border-radius:28px">进入新栏目 →</a></div>
    </div>
    <div style="border:1px solid rgba(226,200,115,.28);background:rgba(15,11,31,.58);padding:28px 25px;box-shadow:0 22px 60px rgba(0,0,0,.22)">
      <div style="font-size:11px;letter-spacing:.34em;color:#e2c873;margin-bottom:18px">一 篇 纲 领 论 文 必 须 交 出</div>
      <div style="display:grid;gap:14px">
        <div style="border-left:3px solid #8d74e5;padding-left:14px"><b style="display:block;color:#fff4d8">新对象</b><span style="font-size:13px;color:#bfb5cc">此前没有稳定字段的研究对象</span></div>
        <div style="border-left:3px solid #5f91b9;padding-left:14px"><b style="display:block;color:#fff4d8">新测量</b><span style="font-size:13px;color:#bfb5cc">可执行读数、反事实与独立数据源</span></div>
        <div style="border-left:3px solid #c16062;padding-left:14px"><b style="display:block;color:#fff4d8">真对手</b><span style="font-size:13px;color:#bfb5cc">最强近邻与会使理论失败的条件</span></div>
        <div style="border-left:3px solid #d0a84f;padding-left:14px"><b style="display:block;color:#fff4d8">后续路径</b><span style="font-size:13px;color:#bfb5cc">可以被独立团队接续的研究工程</span></div>
      </div>
      <div style="margin-top:22px;padding-top:18px;border-top:1px solid rgba(226,200,115,.2);font-size:12.5px;line-height:1.8;color:#a99db8">相关论文：合位 · 无主段 · 同缩 · 同持 · 复位序 · 持锁位 · 无人承担项</div>
    </div>
  </div>
</section>
<style>@media(max-width:780px){{#programmatic-innovation-feature>div{{grid-template-columns:1fr!important}}}}</style>
'''


def patch_home() -> bool:
    raw = HOME.read_text(encoding='utf-8')
    changed = False
    if NAV_MARK not in raw:
        anchor = '<a href="/frontier/" class="zh-only"'
        pos = raw.find(anchor)
        if pos < 0:
            raise RuntimeError('Homepage frontier navigation anchor not found')
        raw = raw[:pos] + NAV + raw[pos:]
        changed = True
    if FEATURE_MARK not in raw:
        anchor = '<!-- 健脑三件'
        pos = raw.find(anchor)
        if pos < 0:
            # Stable fallback: place before the first feature section after hero.
            anchor = '<!-- TOP FEATURE BANNER'
            pos = raw.find(anchor)
        if pos < 0:
            raise RuntimeError('Homepage feature insertion anchor not found')
        raw = raw[:pos] + FEATURE + '\n' + raw[pos:]
        changed = True
    if changed:
        HOME.write_text(raw, encoding='utf-8')
    return changed


def patch_search_builder() -> bool:
    raw = SEARCH_BUILDER.read_text(encoding='utf-8')
    if '"programmatic-innovation": "纲领创新"' in raw:
        return False
    anchor = '    "frontier": "新思想前沿",\n'
    if anchor not in raw:
        raise RuntimeError('Search SECTION_LABELS anchor not found')
    raw = raw.replace(anchor, anchor + '    "programmatic-innovation": "纲领创新",\n', 1)
    SEARCH_BUILDER.write_text(raw, encoding='utf-8')
    return True


def sanity_check() -> None:
    required = [
        ROOT/'public/programmatic-innovation/index.html',
        ROOT/'public/programmatic-innovation/occurrence-fidelity/index.html',
        ROOT/'public/programmatic-innovation/recovery-order/index.html',
        ROOT/'public/programmatic-innovation/unassigned-burden/index.html',
        ROOT/'public/confluence/unit-coincidence/index.html',
        ROOT/'public/confluence/unowned-segment/index.html',
        ROOT/'public/confluence/same-shrinkage/index.html',
        ROOT/'public/confluence/co-persistence/index.html',
        ROOT/'public/confluence/lock-holding-position/index.html',
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise RuntimeError('Missing linked pages: ' + ', '.join(missing))
    article = (ROOT/'public/programmatic-innovation/occurrence-fidelity/index.html').read_text(encoding='utf-8')
    cjk = len(re.findall(r'[\u4e00-\u9fff]', re.sub(r'<[^>]+>', '', article)))
    if cjk < 30000:
        raise RuntimeError(f'Opening paper is below 30,000 CJK characters: {cjk}')
    print(f'[OK] opening paper CJK count: {cjk}')


if __name__ == '__main__':
    sanity_check()
    a = patch_home()
    b = patch_search_builder()
    print('homepage patched' if a else 'homepage already current')
    print('search section patched' if b else 'search section already current')
