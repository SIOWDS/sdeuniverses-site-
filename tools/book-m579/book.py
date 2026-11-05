#!/usr/bin/env python3
"""按德麦国际专著第 220、302 号版式排《接、不接与没接》。
用法：python3 book.py word|pdf   两遍排：第一遍取页码，第二遍写目录。"""
import re,sys,os,json,copy,subprocess
from docx import Document
from docx.shared import Pt,Cm,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL,WD_TAB_ALIGNMENT,WD_TAB_LEADER,WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
R='/home/claude/books/jie';OUT=R+'/out';os.makedirs(OUT,exist_ok=True)
MODE=sys.argv[1] if len(sys.argv)>1 else 'word'
SERIF,SANS=('宋体','黑体') if MODE=='word' else ('Noto Serif CJK SC','Noto Sans CJK SC')
LATIN='Times New Roman'
TITLE='接、不接与没接';SUB='一样东西凭什么稳得住'
META=json.load(open(R+'/front/meta.json',encoding='utf8'))
PARTS=json.load(open(R+'/front/parts.json',encoding='utf8'))
ORDER=[('p1',['01','02','03','04']),('p2',['05','06','07','08']),('p3',['09','10','11','12','13','14']),('p4',['15','16','17','18','19','20']),('p5',['21','22','23','24','25']),('p6',['26','27','28','29'])]
INK=(0x1E,0x1E,0x1E);GR=(0x66,0x66,0x66);BLUE=(0x1F,0x3A,0x5F)
CN='零一二三四五六七八九十'
def cn(n):
    return CN[n] if n<=10 else ('十'+(CN[n-10] if n>10 else ''))
def fonts(obj,east,size=None,bold=None,color=None):
    el=obj.element if hasattr(obj,'element') else obj._element
    rpr=el.get_or_add_rPr();rf=rpr.find(qn('w:rFonts'))
    if rf is None:
        rf=OxmlElement('w:rFonts');rpr.insert(0,rf)
    for a in list(rf.attrib):del rf.attrib[a]
    rf.set(qn('w:ascii'),LATIN);rf.set(qn('w:hAnsi'),LATIN);rf.set(qn('w:eastAsia'),east)
    f=obj.font
    if size:f.size=Pt(size)
    if bold is not None:f.bold=bold
    if color:f.color.rgb=RGBColor(*color)
def norm(t):
    t=re.sub(r'第(\d+)章',r'第 \1 章',t)
    return t
def add_runs(p,t,size=None,east=None):
    for part in re.split(r'(\*\*[^*]+\*\*)',norm(t)):
        if not part:continue
        if part.startswith('**'):
            r=p.add_run(part[2:-2]);fonts(r,SANS,size,True)
        else:
            r=p.add_run(part);fonts(r,east or SERIF,size)
def rule(p,side='bottom',color='999999'):
    pPr=p._p.get_or_add_pPr();bd=OxmlElement('w:pBdr');b=OxmlElement('w:'+side)
    b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),color);b.set(qn('w:space'),'4');bd.append(b);pPr.append(bd)
def field(par,instr,size=9):
    def r(t=None,kind=None):
        run=par.add_run();fonts(run,SERIF,size,color=GR)
        if kind:
            fc=OxmlElement('w:fldChar');fc.set(qn('w:fldCharType'),kind);run._r.append(fc)
        elif t:
            it=OxmlElement('w:instrText');it.set(qn('xml:space'),'preserve');it.text=t;run._r.append(it)
    r(kind='begin');r(t=instr);r(kind='separate')
    ph=par.add_run('1');fonts(ph,SERIF,size,color=GR);r(kind='end')
_bid=[100]
def bkname(t):
    import hashlib
    return 'toc_'+hashlib.md5(re.sub(r'\s+','',t).encode()).hexdigest()[:10]
def bookmark(p,t):
    _bid[0]+=1
    a=OxmlElement('w:bookmarkStart');a.set(qn('w:id'),str(_bid[0]));a.set(qn('w:name'),bkname(t))
    e=OxmlElement('w:bookmarkEnd');e.set(qn('w:id'),str(_bid[0]))
    pos=1 if p._p.pPr is not None else 0
    p._p.insert(pos,a);p._p.append(e)
def pageref(par,t,cached,size=10):
    def r(txt=None,kind=None):
        run=par.add_run();fonts(run,SERIF,size)
        if kind:
            fc=OxmlElement('w:fldChar');fc.set(qn('w:fldCharType'),kind);run._r.append(fc)
        else:
            it=OxmlElement('w:instrText');it.set(qn('xml:space'),'preserve');it.text=txt;run._r.append(it)
    r(kind='begin');r(txt=' PAGEREF %s \\h '%bkname(t));r(kind='separate')
    ph=par.add_run(str(cached));fonts(ph,SERIF,size);r(kind='end')
def section_break(doc,kind='nextPage'):
    p=doc.add_paragraph();pPr=p._p.get_or_add_pPr()
    s=copy.deepcopy(doc.element.body.find(qn('w:sectPr')))
    for c in list(s):
        if c.tag in (qn('w:headerReference'),qn('w:footerReference'),qn('w:pgNumType'),qn('w:titlePg')):s.remove(c)
    t=s.find(qn('w:type'))
    if t is None:
        t=OxmlElement('w:type');s.insert(0,t)
    t.set(qn('w:val'),kind);pPr.append(s);p.paragraph_format.space_after=Pt(0);return p
def pgnum(section,fmt,start=None):
    s=section._sectPr;pg=s.find(qn('w:pgNumType'))
    if pg is None:
        pg=OxmlElement('w:pgNumType');s.append(pg)
    pg.set(qn('w:fmt'),fmt)
    if start is not None:pg.set(qn('w:start'),str(start))
def table(d,rows):
    t=d.add_table(rows=len(rows),cols=len(rows[0]))
    tblPr=t._tbl.tblPr
    b=OxmlElement('w:tblBorders')
    for e,sz in (('top','8'),('bottom','8'),('insideH','2')):
        x=OxmlElement('w:'+e);x.set(qn('w:val'),'single');x.set(qn('w:sz'),sz);x.set(qn('w:color'),'555555' if sz=='8' else 'BBBBBB');b.append(x)
    tblPr.append(b)
    w=tblPr.find(qn('w:tblW'))
    if w is None:
        w=OxmlElement('w:tblW');tblPr.append(w)
    w.set(qn('w:type'),'pct');w.set(qn('w:w'),'5000')
    W={'条目':[2.4,5.6,4.8]}.get(rows[0][0])
    if W and MODE=='reader':W=[x*15.2/12.8 for x in W]
    if W:
        lay=OxmlElement('w:tblLayout');lay.set(qn('w:type'),'fixed');tblPr.append(lay)
        tw=[int(x*567) for x in W]
        for gc,v in zip(t._tbl.tblGrid.findall(qn('w:gridCol')),tw):gc.set(qn('w:w'),str(v))
        for row in t.rows:
            for cell,v in zip(row.cells,tw):
                tc=cell._tc.get_or_add_tcPr();x=tc.find(qn('w:tcW'))
                if x is None:
                    x=OxmlElement('w:tcW');tc.insert(0,x)
                x.set(qn('w:type'),'dxa');x.set(qn('w:w'),str(v))
    for i,r in enumerate(rows):
        for j,c in enumerate(r):
            cell=t.cell(i,j);p=cell.paragraphs[0];p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1.25;p.paragraph_format.space_after=Pt(1);p.alignment=AL.LEFT
            if i==0:
                tc=cell._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:val'),'clear');sh.set(qn('w:fill'),'EEF2F6');tc.append(sh)
                rr=p.add_run(c);fonts(rr,SANS,8.5,True)
            else:add_runs(p,c,8.5)
    sp=d.add_paragraph();sp.paragraph_format.space_after=Pt(4)
def setup(d):
    s=d.sections[0];s.page_width,s.page_height=(Cm(19),Cm(25)) if MODE=='reader' else (Cm(17),Cm(24))
    s.left_margin=s.right_margin=Cm(1.9) if MODE=='reader' else Cm(2.1);s.top_margin,s.bottom_margin=Cm(2.3),Cm(2.1);s.header_distance=s.footer_distance=Cm(1.2)
    S=d.styles;fonts(S['Normal'],SERIF,12 if MODE=='reader' else 10.5,color=INK)
    pf=S['Normal'].paragraph_format;pf.line_spacing=1.55;pf.first_line_indent=Pt(24 if MODE=='reader' else 21);pf.space_after=Pt(3);pf.alignment=AL.JUSTIFY
    for n,sz in (('Heading 1',22),('Heading 2',17),('Heading 3',12)):
        fonts(S[n],SANS,sz,True,INK if n!='Heading 3' else BLUE);S[n].paragraph_format.keep_with_next=True;S[n].paragraph_format.first_line_indent=Pt(0)
    a=S['Heading 1'].paragraph_format;a.page_break_before=True;a.alignment=AL.CENTER;a.space_before=Pt(120);a.space_after=Pt(30)
    a=S['Heading 2'].paragraph_format;a.space_before=Pt(4);a.space_after=Pt(18);a.alignment=AL.LEFT
    a=S['Heading 3'].paragraph_format;a.space_before=Pt(2);a.space_after=Pt(6);a.alignment=AL.LEFT
def plain(d,t):
    p=d.add_paragraph();add_runs(p,t);return p
def h2(d,text,num=None):
    if num is not None:
        n=d.add_paragraph();n.paragraph_format.page_break_before=True;n.paragraph_format.first_line_indent=Pt(0);n.paragraph_format.space_before=Pt(30);n.paragraph_format.space_after=Pt(0);n.paragraph_format.keep_with_next=True;n.alignment=AL.LEFT
        r=n.add_run('%02d'%num);fonts(r,SANS,54,True,(0xC9,0xD3,0xDE))
    p=d.add_paragraph(style='Heading 2')
    if num is None:p.paragraph_format.page_break_before=True
    r=p.add_run(norm(text));fonts(r,SANS,17,True,INK);rule(p);bookmark(p,norm(text));return p
def h3(d,i,text):
    m=d.add_paragraph();m.alignment=AL.LEFT;m.paragraph_format.first_line_indent=Pt(0);m.paragraph_format.space_before=Pt(12);m.paragraph_format.space_after=Pt(0);m.paragraph_format.keep_with_next=True
    r=m.add_run('◆');fonts(r,SERIF,9,color=BLUE)
    p=d.add_paragraph(style='Heading 3');t=(cn(i)+'、'+text) if (i and not re.match(r'^[一二三四五六七八九十]+、',text)) else text
    r=p.add_run(norm(t));fonts(r,SANS,12,True,BLUE)
def question(d,t):
    p=d.add_paragraph();p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_before=Pt(2);p.paragraph_format.space_after=Pt(14);p.paragraph_format.line_spacing=1.4;p.alignment=AL.LEFT
    a,b=t.split('：',1);r=p.add_run(a+'：');fonts(r,SANS,10.5,True,BLUE);r=p.add_run(norm(b));fonts(r,SERIF,10.5,color=(0x44,0x44,0x44))
    pPr=p._p.get_or_add_pPr();sh=OxmlElement('w:shd');sh.set(qn('w:val'),'clear');sh.set(qn('w:fill'),'F3F5F8');pPr.append(sh)
def body(d,lines,number=True):
    i=0;k=0
    while i<len(lines):
        l=lines[i].rstrip()
        if not l:i+=1;continue
        if l.startswith('## '):
            k+=1;h3(d,k if number else 0,l[3:].strip())
        elif l.startswith('这一章的问题：'):question(d,l)
        elif l.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                c=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',x) for x in c):rows.append(c)
                i+=1
            table(d,rows);continue
        else:
            p=plain(d,l)
            if l.startswith(('**这一章说了什么','**回家看一眼')):
                p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_before=Pt(8)
        i+=1
def chapter(d,key):
    L=open(f'{R}/chapters/{key}.md',encoding='utf8').read().split('\n')
    title=L[0].lstrip('# ').strip();m=re.match(r'第(\d+)章　(.*)',title)
    if m:
        h2(d,f'第 {m.group(1)} 章　{m.group(2)}',int(m.group(1)))
    else:h2(d,title)
    body(d,L[1:]);return title
def mdfile(d,path,number=False):
    txt=open(path,encoding='utf8').read().split('\n# ')
    for n,chunk in enumerate(txt):
        chunk=chunk.lstrip('# ').split('\n');h2(d,chunk[0].strip());body(d,chunk[1:],number)
def build(pm):
    d=Document();setup(d)
    def c(t,size,east,bold=False,color=INK,before=0,after=6):
        p=d.add_paragraph();p.alignment=AL.CENTER;p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_before=Pt(before);p.paragraph_format.space_after=Pt(after)
        r=p.add_run(t);fonts(r,east,size,bold,color);return p
    c(TITLE,34,SANS,True,before=100,after=14);c(SUB,15,SANS,False,(0x44,0x44,0x44),after=60)
    c('王德生　黄倩盈　著',14,SERIF,after=150);c('德麦国际出版社',12,SANS,True,after=2);c('Demai International Press',10,SERIF,after=2);c('新加坡',10,SERIF,after=0)
    section_break(d)
    p0=d.add_paragraph();p0.paragraph_format.space_before=Pt(120);p0.paragraph_format.space_after=Pt(0)
    for k,v in META['rows']:
        p=d.add_paragraph();p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1.45;p.paragraph_format.space_after=Pt(1);p.alignment=AL.LEFT
        r=p.add_run(k+'：');fonts(r,SANS,9.5,True);r=p.add_run(v);fonts(r,SERIF,9.5)
    p=d.add_paragraph();p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_before=Pt(10);p.paragraph_format.line_spacing=1.45
    r=p.add_run('AI 协作声明：');fonts(r,SANS,9,True);r=p.add_run(META['ai']);fonts(r,SERIF,9,color=(0x44,0x44,0x44))
    for f,num in (('作者介绍',False),('前言',True),('导读',False)):
        mdfile(d,f'{R}/front/{f}.md',num)
    # 目录
    tp=d.add_paragraph();tp.paragraph_format.page_break_before=True;tp.paragraph_format.first_line_indent=Pt(0);tp.paragraph_format.space_after=Pt(16)
    r=tp.add_run('目录');fonts(r,SANS,17,True)
    ents=[]
    ents.append((2,open(R+'/chapters/00.md',encoding='utf8').readline().lstrip('# ').strip()))
    for pk,chs in ORDER:
        ents.append((1,PARTS[pk][0]))
        for k in chs:ents.append((2,re.sub(r'第(\d+)章',r'第 \1 章',open(f'{R}/chapters/{k}.md',encoding='utf8').readline().lstrip('# ').strip())))
    ents.append((2,open(R+'/chapters/30.md',encoding='utf8').readline().lstrip('# ').strip()))
    back=[]
    for f in ('back.md','appendix2.md'):
        pth=f'{R}/front/{f}'
        if os.path.exists(pth):
            for l in open(pth,encoding='utf8'):
                if l.startswith('# '):back.append(l[2:].strip())
    backorder=sorted(back,key=lambda x:(0 if x.startswith('参考') else 2 if x=='后记' else 1))
    for b in backorder:ents.append((3,b))
    for kind,t in ents:
        p=d.add_paragraph();pf=p.paragraph_format;pf.first_line_indent=Pt(0);pf.line_spacing=1.28;pf.alignment=AL.LEFT
        pf.tab_stops.add_tab_stop(Cm(15.2 if MODE=='reader' else 12.8),WD_TAB_ALIGNMENT.RIGHT,WD_TAB_LEADER.DOTS)
        if kind==1:
            pf.space_before=Pt(8);pf.space_after=Pt(2);r=p.add_run(t);fonts(r,SANS,10.5,True)
        else:
            pf.left_indent=Cm(0.6 if kind==2 else 0);pf.space_after=Pt(1);r=p.add_run(t);fonts(r,SERIF,10)
        r=p.add_run('\t');fonts(r,SERIF,10);pageref(p,t,pm.get(t,''))
    section_break(d)
    # 正文
    def part(k):
        p=d.add_paragraph(style='Heading 1');a,b=PARTS[k][0].split('　',1);r=p.add_run(a);fonts(r,SANS,22,True);r.add_break()
        r2=p.add_run(b);fonts(r2,SANS,16,False,(0x44,0x44,0x44));bookmark(p,PARTS[k][0])
        for x in PARTS[k][1:]:plain(d,x)
    fp=True
    chapter(d,'00')
    d.paragraphs[-1]
    for pk,chs in ORDER:
        part(pk)
        for k in chs:chapter(d,k)
    chapter(d,'30')
    # 书末：参考书目—附录—后记
    blocks={}
    for f in ('back.md','appendix2.md'):
        pth=f'{R}/front/{f}'
        if os.path.exists(pth):
            for ch in ('\n'+open(pth,encoding='utf8').read()).split('\n# ')[1:]:
                ls=ch.split('\n');blocks[ls[0].strip()]=ls[1:]
    for b in backorder:
        h2(d,b);body(d,blocks[b],False)
    # 分节设置
    secs=d.sections
    pgnum(secs[0],'lowerRoman',1);pgnum(secs[1],'lowerRoman',2);pgnum(secs[2],'decimal',1)
    eo=OxmlElement('w:evenAndOddHeaders');d.settings.element.append(eo)
    for i,s in enumerate(secs):
        s.different_first_page_header_footer=False
        for x in (s.header,s.footer,s.even_page_header,s.even_page_footer):x.is_linked_to_previous=False
        if i==0:continue
        ph=s.even_page_header.paragraphs[0];ph.alignment=AL.LEFT;ph.paragraph_format.first_line_indent=Pt(0);r=ph.add_run(TITLE);fonts(r,SERIF,9,color=GR);rule(ph)
        po=s.header.paragraphs[0];po.alignment=AL.RIGHT;po.paragraph_format.first_line_indent=Pt(0)
        if i==1:
            r=po.add_run(TITLE);fonts(r,SERIF,9,color=GR)
        else:field(po,' STYLEREF "Heading 2" ')
        rule(po)
        for f in (s.footer,s.even_page_footer):
            pf=f.paragraphs[0];pf.alignment=AL.CENTER;pf.paragraph_format.first_line_indent=Pt(0);field(pf,' PAGE ')
    d.core_properties.title=TITLE+'：'+SUB;d.core_properties.author='王德生 黄倩盈'
    out=f'{OUT}/接、不接与没接-{MODE}.docx';d.save(out);return out,[t for _,t in ents if _!=0]
def topdf(p):
    subprocess.run(['soffice','-env:UserInstallation=file:///tmp/lo_'+MODE,'--headless','--convert-to','pdf',p,'--outdir',OUT],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1200)
    return p[:-5]+'.pdf'
def pagemap(pdf,titles):
    txt=subprocess.run(['pdftotext','-layout',pdf,'-'],capture_output=True,text=True).stdout.split('\f')
    N=[re.sub(r'\s+','',x) for x in txt]
    toc=next(i for i,x in enumerate(N) if x.startswith('目录') or '目录导论' in x[:40])
    # 目录可能占两页，正文第一页＝导论页
    key=re.sub(r'\s+','',titles[0])
    start=next(i for i in range(toc+1,len(N)) if key in N[i] and '………' not in N[i] and '....' not in N[i])
    pm={};cur=start
    for t in titles:
        k=re.sub(r'\s+','',t).split('　')[-1] if t.startswith('第') and '编' in t[:3] else re.sub(r'\s+','',t)
        for i in range(cur,len(N)):
            head=N[i][:200]
            if k in head:
                pm[t]=i-start+1;cur=i;break
    return pm,len(N)
if __name__=='__main__':
    out,titles=build({})
    pdf=topdf(out);pm,n=pagemap(pdf,titles)
    out,_=build(pm)
    json.dump(pm,open(OUT+'/pm-%s.json'%MODE,'w'),ensure_ascii=False,indent=0)
    pdf=topdf(out);pm2,n=pagemap(pdf,titles)
    print(out,n,'missing',[t for t in titles if t not in pm],'shift',[t for t in titles if pm.get(t)!=pm2.get(t)][:5])
