# -*- coding: utf-8 -*-
import json, sys, importlib.util, os

spec=importlib.util.spec_from_file_location("gen","/home/claude/site/tools/gen_app_page.py")
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

ACCENT={'red':'#8A2E2E','red2':'#6E2222','line':'rgba(138,46,46,0.16)','ink_red':'#D89A9A'}
SEED_URL="/column/power-genesis-3/"
SEED_LABEL="改命的工程学"
BYLINE="Claude 著 · 依王德生《SDE本体论》 · SDE UNIVERSES · 2026年7月 · 全文约 1.0 万字"

# slug -> (domain_label, sibling info)
PAGES={
 'education':{'json':'edu.json','slug':'power-genesis-3-education','eyebrow':'改命的工程学 · 三大主权应用 · 教育篇','domain':'教育'},
 'health':   {'json':'health.json','slug':'power-genesis-3-health','eyebrow':'改命的工程学 · 三大主权应用 · 健康篇','domain':'健康'},
 'business': {'json':'biz.json','slug':'power-genesis-3-business','eyebrow':'改命的工程学 · 三大主权应用 · 商业与经济篇','domain':'商业·经济'},
}
TITLES={ # for nextbox cross-links, short labels
 'education':'教育：帮孩子夺回三大主权',
 'health':'健康：夺回你对身体的三大主权',
 'business':'商业与经济：夺回你和组织的三大主权',
}
ORDER=['education','health','business']

for key in ORDER:
    P=PAGES[key]
    d=json.load(open('/home/claude/site/drafts/'+P['json'],encoding='utf-8'))
    # nextbox: back to seed + other two siblings
    others=[k for k in ORDER if k!=key]
    links=[(f"回主文 · {SEED_LABEL}", SEED_URL)]
    for o in others:
        links.append((TITLES[o], f"/column/{PAGES[o]['slug']}/"))
    meta={
      'accent':ACCENT,
      'slug':P['slug'],
      'title':f"{d['h1']} · 改命的工程学{P['domain']}应用 | SDE Universes",
      'desc':(d['deck'][:150].replace('"','')),
      'og':d['h1'],
      'back_url':SEED_URL,'back_label':SEED_LABEL,
      'eyebrow':P['eyebrow'],
      'h1':d['h1'],'sub':d['sub'],'byline':BYLINE,
      'deck':d['deck'],'motif':d['motif'],
      'nextbox':{
        'kicker':'改命的工程学 · 一颗种子，三处现场',
        'h4':'同一套工序，落进三个现场',
        'p':'教育、健康、商业与经济——三篇应用长文用同一副工程学的眼睛，把《改命的工程学》里的三大主权、四种结局、九十天节拍，各自落到一个可照做的现场。',
        'links':links,
      },
      'scholarly':{
        'materials':d['materials'],
        'chain':d['chain'],
        'closing':d['closing'],
      },
      'refs':d['refs'],
    }
    html=gen.build_page(meta, d['body_html'])
    outdir=f"/home/claude/site/public/column/{P['slug']}"
    os.makedirs(outdir,exist_ok=True)
    open(outdir+"/index.html","w",encoding='utf-8').write(html)
    print(f"WROTE {P['slug']}/index.html  ({len(html)} bytes)")
print("done")
