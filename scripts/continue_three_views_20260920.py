#!/usr/bin/env python3
"""Publish omitted diagram sources; separate platform chrome without losing source text."""
from __future__ import annotations
import hashlib, html, io, json, math, re, shutil
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import fitz
from PIL import Image

VERSION = '20260920-longform-v2'
H = html.escape
COMMENT = re.compile(r'^全部评论[（(]\d+条[）)]$')
UI = [re.compile(x) for x in [
    r'^[•·●]$', r'^赞赏\d+(?:\.\d+)?元$', r'^共被阅读[\d,]+次$',
    r'^.{1,20}赞赏了这条(?:话题|评论)$', r'^你可能错过的话题$',
    r'^点击查看$', r'^三视角学员免费，请微信华小明或行者，做延期一年[。.]?$'
]]
EDUCATION_ROWS = [
    ('本质', '全人教育', '心（真善美）；灵（信望爱）；身（知意情）'),
    ('本质', '终生教育', '三视角智慧教育；成长心态教育；学科通融'),
    ('本质', '创造性教育', '无痕教育；社会性建构；建构式学习'),
    ('价值', '存在感', '使命；生命场；核心竞争力'),
    ('价值', '价值感', '信；爱；望'),
    ('价值', '成就感', '智商；情商；意商'),
    ('教学', '内容', '对比；分布；变化'),
    ('教学', '激励', '好奇；联想；批判'),
    ('教学', '过程', '类比；归纳；演绎'),
]
SPECS = [
    dict(code='b121', title='教育27宫格', category='教育智慧', cat='education',
         pages=1, useful=[1], author='王德生',
         excerpt='教育图示资料：本质、价值、教学三大分支，九组结构和二十七项标注。保留完整原图，并提供可复制的上图文字对照表。'),
    dict(code='b162', title='汉字树人', category='学科学习法', cat='learning',
         pages=6, useful=[3,4,5], author='原图署名见原稿',
         excerpt='原稿为《汉字树》相关图片资料：封面、局部构形关系图、全幅关系图。三幅有效图示连续阅读，三个空白页不占用网页阅读位置。')
]

def compact(s: str) -> str:
    return re.sub(r'\s+', '', s)

def load(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))

def write(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding='utf-8')

def page_for(root: Path, url: str) -> Path:
    if not url.startswith('/three-views/') or '..' in url:
        raise ValueError('Unexpected document URL: ' + url)
    return root / 'public' / url.lstrip('/') / 'index.html'

def clean_one(path: Path, record: dict) -> dict | None:
    raw = path.read_text(encoding='utf-8')
    soup = BeautifulSoup(raw, 'html.parser')
    prose = soup.select_one('.prose')
    if prose is None or prose.get('data-cleanup-version') == VERSION:
        return None
    children = [x for x in prose.children if isinstance(x, Tag)]
    # An isolated instruction inside an article is not enough to trigger cleanup.
    footer = next((i for i,x in enumerate(children)
                   if COMMENT.fullmatch(compact(x.get_text())) or
                   compact(x.get_text()) == '你可能错过的话题' or
                   re.fullmatch(r'赞赏\d+(?:\.\d+)?元', compact(x.get_text()))), None)
    if footer is None:
        return None
    removed, kept, discussion = [], [], []
    marker = False
    for i, node in enumerate(children):
        text = compact(node.get_text())
        if i >= footer and node.name in ('p','h2','h3') and COMMENT.fullmatch(text):
            removed.append(node.get_text()); node.decompose(); marker = True
            continue
        if i >= footer and node.name == 'p' and any(p.fullmatch(text) for p in UI):
            removed.append(node.get_text()); node.decompose()
            continue
        kept.append(str(node))
        if marker:
            if node.name in ('p','h2','h3','h4','blockquote','ul','ol'):
                discussion.append(node)
            else:
                marker = False
    if not removed:
        return None
    # All retained original DOM nodes must remain identical, including comments.
    expected = hashlib.sha256(''.join(kept).encode()).hexdigest()
    if discussion:
        panel = soup.new_tag('details', attrs={'class':'source-discussion'})
        label = soup.new_tag('summary'); label.string = '原稿讨论（历史记录）'
        panel.append(label)
        discussion[0].insert_before(panel)
        for node in discussion:
            panel.append(node.extract())
    actual_nodes = []
    for node in prose.children:
        if not isinstance(node, Tag):
            continue
        if 'source-discussion' in node.get('class', []):
            actual_nodes.extend(str(x) for x in node.children if isinstance(x, Tag) and x.name != 'summary')
        else:
            actual_nodes.append(str(node))
    actual = hashlib.sha256(''.join(actual_nodes).encode()).hexdigest()
    if expected != actual:
        raise AssertionError('Retained source content changed: ' + str(path))
    prose['data-cleanup-version'] = VERSION
    prose['data-preserved-content-check'] = 'passed'
    record['cleanup_removed_ui_lines'] = len(removed)
    record['cleanup_discussion_folded'] = bool(discussion)
    record['cleanup_version'] = VERSION
    record['chars'] = len(compact(prose.get_text()))
    record['reading_minutes'] = max(1, math.ceil(record['chars']/500))
    for node in children[:6]:
        if not node.parent:
            continue
        match = re.fullmatch(r'(?:作者|分享者)[：:\s]+([\u4e00-\u9fff·]{2,8})', node.get_text().strip())
        if match:
            record['author'] = match.group(1)
            break
    meta = soup.select_one('.article-head .meta')
    if meta:
        meta.string = f"{record.get('author','署名见原稿')}　·　正文约 {record['chars']:,} 字　·　约 {record['reading_minutes']} 分钟"
    write(path, str(soup))
    return dict(url=record['url'], removed_ui_lines=removed,
                discussion_preserved=bool(discussion), retained_content_sha256=actual,
                retention_check='passed')

def render_source(root: Path, spec: dict) -> tuple[list[dict],str]:
    directory = root/'public'/'three-views'/'doc'/spec['code']
    pdf = directory/(spec['code']+'.pdf')
    digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
    doc = fitz.open(pdf)
    if len(doc) != spec['pages']:
        raise AssertionError('Source page count changed: ' + str(pdf))
    for number in range(1, len(doc)+1):
        if number not in spec['useful']:
            page = doc[number-1]
            if page.get_text().strip() or page.get_images(full=True):
                raise AssertionError('A supposedly blank page contains content')
    figures = []
    for page_number in spec['useful']:
        page = doc[page_number-1]
        images = page.get_images(full=True)
        if spec['code']=='b162' and len(images)==1:
            source = doc.extract_image(images[0][0])['image']
            image = Image.open(io.BytesIO(source)).convert('RGB')
            if page_number==5 and image.height>image.width:
                image = image.rotate(90, expand=True)
        else:
            image = page.get_pixmap(matrix=fitz.Matrix(2.2,2.2), alpha=False).pil_image().convert('RGB')
        asset = directory/'web'/f'page-{page_number:03d}.webp'
        asset.parent.mkdir(parents=True,exist_ok=True)
        image.save(asset, format='WEBP', lossless=True, method=6)
        figures.append(dict(page=page_number,url='/'+asset.relative_to(root/'public').as_posix(),width=image.width,height=image.height))
    if hashlib.sha256(pdf.read_bytes()).hexdigest()!=digest:
        raise AssertionError('Original PDF was modified')
    return figures,digest

def diagram_page(root: Path, spec: dict) -> dict:
    directory = root/'public'/'three-views'/'doc'/spec['code']
    index = directory/'index.html'
    original = directory/'original.html'
    if not original.exists():
        shutil.copyfile(index, original)
    figures,pdf_sha = render_source(root,spec)
    url=f"/three-views/doc/{spec['code']}/"
    toc = '<li><a href="#source-figures">原稿图示</a></li><li><a href="#reading-note">资料说明</a></li>'
    if spec['code']=='b121':
        rows=''.join('<tr>'+''.join(f'<td>{H(cell)}</td>' for cell in row)+'</tr>' for row in EDUCATION_ROWS)
        body='<section id="reading-note"><h2>资料说明</h2><p>本资料原件为一页图示，上半页是以“21世纪教育”为中心的教育结构，下半页是“三视角27宫格”总图。以下为上半页的文字对照整理，供检索、复制和小屏阅读；图中的位置、连线及下半页总图请核对原图。</p></section><section id="transcription"><h2>教育图示：九组结构与二十七项标注</h2><div style="overflow-x:auto"><table><caption>上半页教育图示文字对照（编者转录）</caption><thead><tr><th scope="col">主分支</th><th scope="col">小三角</th><th scope="col">三项标注</th></tr></thead><tbody>'+rows+'</tbody></table></div><p>原图署名：发明人，王德生。表格是图示的文字辅助，不是另写的文章，也不取代原图。</p></section>'
        toc += '<li><a href="#transcription">文字对照表</a></li>'
        captions=['教育27宫格原图：上半页教育结构，下半页三视角27宫格总图。']
    else:
        body='<section id="reading-note"><h2>资料说明</h2><p>原稿是六页幻灯片转换的 PDF，没有可提取的文字层。核对上传的幻灯片后，第1、2、6页为空白；第3、4、5页分别为《汉字树》相关封面、局部关系图和全幅关系图。</p><p>本页按三幅有效图示连续呈现，不把空白页当作文章内容。全幅关系图已转正便于阅读；原始六页 PDF 及原阅读器仍可核对。</p><p>这是图像学习资料，不是王德生署名的文字论文。图中书籍及图像的署名以原图为准；本页说明为编者资料说明，不冒充原作者正文。</p></section>'
        captions=['原稿第3页：《汉字树》相关封面。','原稿第4页：局部构形关系图，点击图片可放大核对。','原稿第5页：全幅汉字树关系图，已将横向图转正。']
    gallery='<section id="source-figures"><h2>原稿图示 · 连续阅读</h2>'
    for f,caption in zip(figures,captions):
        gallery+=f'<figure><a href="{f["url"]}" target="_blank" rel="noopener"><img src="{f["url"]}" width="{f["width"]}" height="{f["height"]}" alt="{H(caption)}" loading="lazy" decoding="async" style="width:100%;height:auto"></a><figcaption>{H(caption)}</figcaption></figure>'
    gallery+='</section>'
    meta=f"图示资料　·　原稿 {spec['pages']} 页　·　{len(figures)} 幅有效图示"
    structured=json.dumps({'@context':'https://schema.org','@type':'CreativeWork','name':spec['title'],'url':'https://sdeuniverses.com'+url,'inLanguage':'zh-CN','isPartOf':{'@type':'CollectionPage','name':'三视角专栏','url':'https://sdeuniverses.com/three-views/'}},ensure_ascii=False)
    document=f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{H(spec['title'])}｜三视角专栏</title><meta name="description" content="{H(spec['excerpt'])}"><link rel="canonical" href="https://sdeuniverses.com{url}"><meta property="og:title" content="{H(spec['title'])}"><meta property="og:url" content="https://sdeuniverses.com{url}"><link rel="stylesheet" href="/three-views/longform/reading.css?v={VERSION}"><style>.reading table{{width:100%;border-collapse:collapse;font-size:1rem}}.reading td,.reading th{{padding:.65rem;border:1px solid #a99979;text-align:left}}.reading figure{{margin:2rem 0}}.reading figcaption{{font-size:.9rem;margin-top:.6rem;line-height:1.7}}.reading section{{scroll-margin-top:7rem}}.reading p{{line-height:1.95}}</style><script type="application/ld+json">{structured}</script></head>
<body id="top"><a class="skip" href="#content">跳到正文</a><div class="progress" aria-hidden="true"></div><header class="top"><a class="brand" href="/three-views/">三视角专栏<small>THREE VIEWS · SDE UNIVERSES</small></a><nav aria-label="主导航"><a href="/three-views/longform/">网页长文</a><a href="/three-views/library/">分类文库</a><a href="/three-views/atlas/">图册</a><a href="/browse/">SDE 首页</a></nav></header><main class="shell"><header class="article-head"><div class="eyebrow">{H(spec['category'])} · 图示资料</div><h1>{H(spec['title'])}</h1><div class="meta">{meta}</div><div class="tools"><a href="{url}original.html">在线翻阅原稿</a><a href="{url}{spec['code']}.pdf" download>下载原稿 PDF</a><button data-size="-1" aria-label="缩小字号">A−</button><button data-size="1" aria-label="放大字号">A＋</button><button data-theme aria-label="切换明暗模式">明暗切换</button></div><p class="notice">图示直接呈现在网页，不依赖 PDF 阅读器载入。原稿及下载入口保留，编者说明与原图内容分开。</p><details class="mobile-toc"><summary>本文目录</summary><ol>{toc}</ol></details></header><div class="layout"><article class="reading" id="content">{body}{gallery}<p><a href="/three-views/library/{spec['cat']}/">返回{H(spec['category'])}</a> · <a href="/three-views/longform/">返回完整目录</a></p></article><aside class="toc"><h2>本页目录</h2><ol>{toc}</ol></aside></div></main><footer class="footer"><p>三视角专栏 · 原图署名见资料 · <a href="/three-views/">返回专栏首页</a></p></footer><script defer src="/three-views/longform/reading.js?v={VERSION}"></script><script defer src="/wds-mode.js?v=20260916a"></script></body></html>'''
    write(index,document)
    return dict(title=spec['title'],url=url,canonical=url,category=spec['category'],author=spec['author'],chars=0,reading_minutes=1,kind='图示资料',pdf=url+spec['code']+'.pdf',source_pages=spec['pages'],image_only_pages=len(figures),figures=len(figures),excerpt=spec['excerpt'],pdf_sha256=pdf_sha,blank_source_pages_omitted=[x for x in range(1,spec['pages']+1) if x not in spec['useful']],editorial_note_separate=True,media_urls=[x['url'] for x in figures])

def refresh_catalog(root: Path, records: list[dict]):
    path=root/'public/three-views/longform/index.html'
    soup=BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    cards=soup.select_one('.cards')
    if not cards or not soup.select_one('#result-count'):
        raise AssertionError('Catalogue structure changed; refusing replacement')
    cards.clear()
    for r in records:
        small=f"{r.get('chars',0):,} 字 · {r.get('reading_minutes',1)} 分钟"
        if r.get('kind')=='图示资料':
            small=f"{r.get('figures',0)} 幅原稿图示 · 原稿 {r.get('source_pages',0)} 页"
        fragment=f'<article class="card" data-category="{H(r["category"])}"><span class="tag">{H(r["category"])} · {H(r.get("kind","网页长文"))}</span><h2><a href="{H(r["url"])}">{H(r["title"])}</a></h2><p>{H(r.get("excerpt",""))}</p><div class="small">{small}</div></article>'
        cards.append(BeautifulSoup(fragment,'html.parser').article)
    count=len(records); total=sum(r.get('chars',0) for r in records)
    soup.select_one('#result-count').string=str(count)
    meta=soup.select_one('.catalog-head .meta')
    if meta: meta.string=f'{count} 份独立文献 · 正文约 {total/10000:.1f} 万字 · 图示资料单独标明'
    ld=soup.find('script',type='application/ld+json')
    if ld:
        data=json.loads(ld.string);data['@type']='CollectionPage';ld.string=json.dumps(data,ensure_ascii=False)
    note=soup.select_one('#continuation-note')
    if not note:
        note=soup.new_tag('p',id='continuation-note',attrs={'class':'notice'})
        soup.select_one('.catalog-head').append(note)
    note.string='本轮补齐《教育27宫格》《汉字树人》的网页图示；文章中的平台操作杂项与正文分离，有内容的原稿讨论折叠保留。'
    write(path,str(soup))
    for path in [root/'public/three-views/index.html', *sorted((root/'public/three-views/library').rglob('index.html'))]:
        source=path.read_text(encoding='utf-8')
        changed=re.sub(r'(进入网页长文目录\s*→\s*)\d+(\s*篇)',lambda m:m[1]+str(count)+' 份文献',source)
        if changed!=source: write(path,changed)

def verify(root: Path, records: list[dict]):
    urls=[r['url'] for r in records]
    assert len(urls)==len(set(urls)), 'Duplicate catalogue URL'
    for r in records:
        p=page_for(root,r['url']);assert p.is_file(), str(p)
        for media in r.get('media_urls',[]): assert (root/'public'/media.lstrip('/')).is_file(), media
    soup=BeautifulSoup((root/'public/three-views/longform/index.html').read_text(),'html.parser')
    linked=[a['href'] for a in soup.select('.cards .card h2 a')]
    assert linked==urls, 'Catalogue and manifest diverged'
    assert int(soup.select_one('#result-count').get_text())==len(urls)
    for s in SPECS:
        page=page_for(root,f"/three-views/doc/{s['code']}/")
        doc=BeautifulSoup(page.read_text(),'html.parser')
        assert len(doc.select('#source-figures img'))==len(s['useful'])
        assert doc.select_one('link[rel="canonical"]')['href'].endswith(f"/{s['code']}/")
        assert (page.parent/'original.html').is_file()
        assert not doc.find('canvas'), 'New diagram reader must not require PDF canvas'

def run(root: Path, minimum: int=400):
    base=root/'public/three-views/longform'
    records=load(base/'manifest.json');assert len(records)>=minimum
    changed=[]
    for r in records:
        result=clean_one(page_for(root,r['url']),r)
        if result: changed.append(result)
    added=[]
    for spec in SPECS:
        item=diagram_page(root,spec)
        previous=next((i for i,r in enumerate(records) if r['url']==item['url']),None)
        if previous is None: records.append(item);added.append(item['url'])
        else: records[previous]=item
    refresh_catalog(root,records)
    write(base/'manifest.json',json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    verify(root,records)
    report=dict(version=VERSION,catalogue_entries=len(records),restored_diagrams=added,
                cleaned_articles=len(changed),removed_platform_lines=sum(len(x['removed_ui_lines']) for x in changed),
                discussion_appendices=sum(x['discussion_preserved'] for x in changed),
                diagram_images=4,blank_source_pages_omitted=3,all_checks_passed=True,
                original_pdfs_unchanged=True,changes=changed)
    write(base/'continuation-report.json',json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    if (base/'report.json').exists():
        old=load(base/'report.json');old.update(version=VERSION,unique_catalog_entries=len(records),characters=sum(r.get('chars',0) for r in records),figures=sum(r.get('figures',0) for r in records),diagram_entries=sum(r.get('kind')=='图示资料' for r in records),image_only_pages=sum(r.get('image_only_pages',0) for r in records),skipped_pages=[],continuation_report='continuation-report.json')
        old['converted_urls']=old.get('converted_urls',len(records))+len(added)
        write(base/'report.json',json.dumps(old,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='changes'},ensure_ascii=False,indent=2))
    return report

if __name__=='__main__':
    run(Path(__file__).resolve().parents[1])
