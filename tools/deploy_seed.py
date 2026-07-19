# -*- coding: utf-8 -*-
"""整颗种子 → 三篇 apply-* 三模式页部署器（网页+翻书read.html+PDF），并在母文页挂三链接区。
用法：python3 tools/deploy_seed.py <seed_slug> <seed_title> <series_base> <drafts_prefix>
drafts 文件：drafts/<prefix>-edu.json / -health.json / -biz.json
"""
import json, sys, os, re, subprocess, importlib.util

ROOT="/home/claude/site"
spec=importlib.util.spec_from_file_location("genA",f"{ROOT}/tools/gen_apply_page.py")
genA=importlib.util.module_from_spec(spec); spec.loader.exec_module(genA)

BYLINE="只讲方法、技术与操作的实践文 · 约 1.0 万字 · Claude 著 · 依王德生《SDE本体论》"

DOMS=[
 ('education','edu','教育'),
 ('health','health','健康'),
 ('business','biz','商业与经济'),
]

READ_TMPL=open(f"{ROOT}/tools/read_template.html",encoding='utf-8').read()

def kw_for(seed_kw, dom):
    return seed_kw.get(dom, seed_kw.get('_', ''))

def deploy(seed_slug, seed_title, series_base, prefix, kw):
    base=f"{ROOT}/public/column/{seed_slug}"
    made=[]
    for dom, jkey, domlabel in DOMS:
        d=json.load(open(f"{ROOT}/drafts/{prefix}-{jkey}.json",encoding='utf-8'))
        pdf=f"apply-{dom}.pdf"
        meta={
          'title':f"{d['h1']} · {series_base} · {domlabel} | SDE Universes",
          'desc':d['deck'][:150].replace('"','').replace('\n',' '),
          'seed_slug':seed_slug,'seed_title':seed_title,
          'series':f"{series_base} · {domlabel}",
          'art_title':d['h1'],'art_subtitle':d['sub'],'byline':BYLINE,
          'abstract':d['deck'],'keywords':kw[dom],
          'materials':d['materials'],'chain':d['chain'],'closing':d['closing'],'refs':d['refs'],
          'pdf_name':pdf,
        }
        html=genA.build_apply_page(meta, d['body_html'])
        outdir=f"{base}/apply-{dom}"; os.makedirs(outdir,exist_ok=True)
        open(f"{outdir}/index.html","w",encoding='utf-8').write(html)
        # read.html
        rh=(READ_TMPL.replace("__TITLE__", d['h1'])
                     .replace("__SEED_SLUG__", seed_slug)
                     .replace("__DOM__", dom))
        open(f"{outdir}/read.html","w",encoding='utf-8').write(rh)
        # pdf
        subprocess.run([sys.executable, f"{ROOT}/tools/build_apply_pdf.py",
                        f"{outdir}/index.html","-o",f"{outdir}/{pdf}"], check=True)
        han=len(re.findall(r'[一-鿿]', d['body_html']))
        made.append((dom, d['h1'], han))
        print(f"  apply-{dom}: 汉字≈{han} · index+read+pdf 生成")
    hook_seed_page(seed_slug, series_base, made)
    return made

def hook_seed_page(seed_slug, series_base, made):
    f=f"{ROOT}/public/column/{seed_slug}/index.html"
    h=open(f,encoding='utf-8').read()
    if f"apply-education" in h and "apply-app-links" in h:
        print("  母文页已挂 apply 链接区，跳过"); return
    titles={dom:t for dom,t,_ in made}
    links="".join(
      f'    <a href="/column/{seed_slug}/apply-{dom}/" style="display:block;color:#0A66C2;font-weight:700;font-size:15.5px;text-decoration:none;margin:7px 0">{lab}篇 · {titles[dom]} →</a>\n'
      for dom,lab in [('education','教育'),('health','健康'),('business','商业与经济')])
    block=(f'\n<div class="apply-app-links" style="max-width:820px;margin:50px auto 0;padding:24px 30px;'
           f'background:linear-gradient(135deg,#f4fbff,#edf6ff);border:1px solid rgba(79,195,247,0.4);'
           f'border-left:4px solid #0A66C2;border-radius:0 8px 8px 0;font-family:\'Songti SC\',\'Noto Serif SC\',serif">\n'
           f'  <div style="font-size:11.5px;letter-spacing:0.32em;color:#0E7C71;margin-bottom:10px">{series_base} · 三篇应用实践文</div>\n'
           f'  <h3 style="font-size:19px;color:#0F2C4A;margin:0 0 8px;font-weight:800;line-height:1.5">把这套方法，落进你的现场</h3>\n'
           f'  <p style="font-size:14.5px;color:#334155;line-height:1.85;margin:0 0 14px">同一套框架，各自落到一个可照做的现场——每篇约一万字，只讲方法、技术与操作（网页 / 翻书 PDF / 下载）。</p>\n'
           f'{links}</div>\n')
    # 插入锚点：优先在 sde-talk 前，否则 footer 前
    for anc in ['<section id="sde-talk"','<!-- 读者讨论','<footer']:
        i=h.find(anc)
        if i!=-1:
            h2=h[:i]+block+h[i:]
            open(f,"w",encoding='utf-8').write(h2)
            print(f"  母文页已挂 apply 三链接区（锚点 {anc[:20]}）"); return
    print("  !! 母文页未找到插入锚点，需手工挂链接")

if __name__=='__main__':
    seed_slug, seed_title, series_base, prefix = sys.argv[1:5]
    KW=json.loads(sys.argv[5]) if len(sys.argv)>5 else {
      'education':f'{series_base} · 改变率不对称 · 四个水龙头 · 关系体检六步',
      'health':f'{series_base} · 改变率不对称 · 四个水龙头 · 关系体检六步',
      'business':f'{series_base} · 改变率不对称 · 四个水龙头 · 关系体检六步'}
    deploy(seed_slug, seed_title, series_base, prefix, KW)
    print("done")
