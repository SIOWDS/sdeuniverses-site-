# -*- coding: utf-8 -*-
import json, importlib.util, os, re

spec=importlib.util.spec_from_file_location("genA","/home/claude/site/tools/gen_apply_page.py")
genA=importlib.util.module_from_spec(spec); spec.loader.exec_module(genA)

SEED_SLUG="power-genesis-3"; SEED_TITLE="改命的工程学"
BYLINE="只讲方法、技术与操作的实践文 · 约 1.0 万字 · Claude 著 · 依王德生《SDE本体论》"
BASE=f"/home/claude/site/public/column/{SEED_SLUG}"

DOMAINS={
 'education':{'json':'edu.json','series':'改命的工程学 · 教育',
   'kw':'命名权 · 判错权 · 计算权 · 四种结局 · 换名 · 九十天节拍 · 育成判据'},
 'health':{'json':'health.json','series':'改命的工程学 · 健康',
   'kw':'命名权 · 判错权 · 计算权 · 换场五步 · 四种结局 · 燃料审计 · 停止条件'},
 'business':{'json':'biz.json','series':'改命的工程学 · 商业与经济',
   'kw':'命名权 · 判错权 · 计算权 · 目标函数 · 整流工程 · 四种结局 · 九十天节拍'},
}

for dom,cfg in DOMAINS.items():
    d=json.load(open('/home/claude/site/drafts/'+cfg['json'],encoding='utf-8'))
    pdf=f"apply-{dom}.pdf"
    meta={
      'title':f"{d['h1']} · {SEED_TITLE} · {'教育' if dom=='education' else '健康' if dom=='health' else '商业与经济'} | SDE Universes",
      'desc':(d['deck'][:150].replace('"','')),
      'seed_slug':SEED_SLUG,'seed_title':SEED_TITLE,
      'series':cfg['series'],
      'art_title':d['h1'],'art_subtitle':d['sub'],'byline':BYLINE,
      'abstract':d['deck'],'keywords':cfg['kw'],
      'materials':d['materials'],'chain':d['chain'],'closing':d['closing'],'refs':d['refs'],
      'pdf_name':pdf,
    }
    html=genA.build_apply_page(meta, d['body_html'])
    outdir=f"{BASE}/apply-{dom}"
    os.makedirs(outdir,exist_ok=True)
    open(outdir+"/index.html","w",encoding='utf-8').write(html)
    # update read.html <title> if exists
    rp=outdir+"/read.html"
    if os.path.exists(rp):
        rh=open(rp,encoding='utf-8').read()
        rh=re.sub(r'<title>.*?</title>', f"<title>{d['h1']} · 翻页阅读 | SDE Universes</title>", rh, count=1, flags=re.S)
        open(rp,"w",encoding='utf-8').write(rh)
    han=len(re.findall(r'[一-鿿]', d['body_html']))
    print(f"apply-{dom}/index.html 写入 | 正文汉字≈{han} | bytes={len(html)}")
print("done")
