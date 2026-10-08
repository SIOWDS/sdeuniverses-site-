#!/usr/bin/env python3
"""Book398-only card layout and intact mobile cover, verified by geometry tests."""
from pathlib import Path
R=Path(__file__).resolve().parent
p=R/'build.py';s=p.read_text(encoding='utf-8')
marker="assert 'data-unit-action=\"learn\"' in card and '判生' in card"
patch='''# Book398 alone adopts the existing Happiness three-button card layout.
card=card.replace('learn-button','learn-link').replace('class="unit-label"','class="publication-unit-label"')
style="""<style data-m398-unit-card-style>
.book[data-id="m-398"] .publication-unit-actions{display:flex;flex-direction:column;align-items:stretch;gap:7px}
.book[data-id="m-398"] .publication-unit-label{order:0;margin:0 0 2px;font-size:11px;color:var(--muted);letter-spacing:.07em}
.book[data-id="m-398"] .publication-unit-actions>a{display:flex;flex-basis:auto;width:100%;margin:0;min-height:44px;align-items:center;justify-content:center;white-space:normal;text-align:center;overflow-wrap:anywhere;line-height:1.55;padding:8px 7px}
.book[data-id="m-398"] [data-unit-action="read"]{order:1}
.book[data-id="m-398"] [data-unit-action="learn"]{order:2}
.book[data-id="m-398"] [data-unit-action="agent"]{order:3}
.book[data-id="m-398"] .unit-secondary{order:4;display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;margin-top:6px}
</style>"""
card=re.sub(r'<style data-m398-unit-card-style>.*?</style>','',card,flags=re.S)
card=re.sub(r'(<article\\b[^>]*>)',lambda m:m.group(1)+style,card,count=1)
'''
if '# Book398 alone adopts' not in s:
    assert marker in s;s=s.replace(marker,patch+marker);p.write_text(s,encoding='utf-8')
p=R/'unit.css';s=p.read_text(encoding='utf-8')
if '/* mobile cover and non-overlapping status */' not in s:
    s+='''\n/* mobile cover and non-overlapping status */
.hero img{height:auto;object-fit:contain}.row.download{display:flex;gap:10px;align-items:stretch}.row.download>a,.row.download>label{display:inline-flex;align-items:center;padding:8px 12px;border:1px solid var(--line);border-radius:9px;min-height:44px;cursor:pointer}
#status{position:static;left:auto;transform:none;width:auto;margin:12px 0}.lesson-link.active{color:var(--ink);background:#302919;border-left:3px solid var(--gold)}
''';p.write_text(s,encoding='utf-8')
p=R/'test.py';s=p.read_text(encoding='utf-8')
old="card.screenshot(path=str(OUT/'shelf-card.png'))"
new="""boxes=[card.locator('[data-unit-action='+k+']').bounding_box() for k in ['read','learn','agent']]
    check('three distinct vertically stacked full-width card buttons',all(b and b['height']>=44 for b in boxes) and boxes[1]['y']>=boxes[0]['y']+boxes[0]['height'] and boxes[2]['y']>=boxes[1]['y']+boxes[1]['height'])
    card.screenshot(path=str(OUT/'shelf-card.png'))"""
if 'three distinct vertically stacked' not in s:
    assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
p=R/'test.py';s=p.read_text(encoding='utf-8')
old="replies[0]['data']['status']=='received-unverified' and replies[0]['data']['upstreamFinishReason'] is None"
new="len([e for e in replies if e['data']['mode'] in ['hint','diagnose','critique','transfer']])==4 and all(e['data']['status']=='received-unverified' and e['data']['upstreamFinishReason'] is None for e in replies if e['data']['mode'] in ['hint','diagnose','critique','transfer'])"
if old in s:s=s.replace(old,new);p.write_text(s,encoding='utf-8')
elif new not in s:raise RuntimeError('Test context changed')
print('Applied book-scoped layout and mode-bound completion assertions.')
