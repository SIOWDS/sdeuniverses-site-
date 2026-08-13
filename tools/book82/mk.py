import re,html,json,os,sys
sys.path.insert(0,'.')
from extract import extract
BASE='/home/claude/site/public/students/'
CH=[
 (1,'阳涌','yang-yong','coupling-reversibility','耦合可逆性极化','当产出趋同时，分化才刚刚开始','劳动经济学×学习科学×数字不平等研究'),
 (2,'黄倩盈','huang-qianying','unilateral-completion','单方完成式理解','理解所必需的「被打碎」，可以由一个人独自承担',''),
 (3,'何丽霞','he-lixia','reverberation','从「读」到「回响」','被击中却说不出来，不是体验贫乏',''),
 (4,'胡志英','hu-zhiying','forced-rupture','受迫断裂','不是「我发现了知识的缺口」，是「我脚下的价值地基裂开了」',''),
 (5,'胡敏','hu-min','resonance-of-pattern-change','参变回响','中医辨证论治的本体论重述',''),
 (6,'鲍锦朝','bao-jinchao','preemptive-compensation','前置后偿','语感的本质：听者未来补偿在说者身体中的前置发生',''),
 (7,'金华','jin-hua','allo-metabolism','异体化','组织成功如何将认知判断力孕育为寄生于自身的他者',''),
 (8,'高鹏','gao-peng','painless-necrosis','无痛之死','现代专业教育中生成性经验的系统性排除',''),
 (9,'秦莉','qin-li','guarding-drift','守卫的漂移','论艺术中「存在论级差」的持存与消逝',''),
 (10,'张琼','zhang-qiong','sedimented-layer','沉淀的形态','伦理生活的「过后」与「之前」',''),
]
DROP=re.compile(r'^(SDE 创新智商|创新智商|盲评|依五维|五维为|本文的那一刀|导读|读这篇|① 理论母文|② 诠释文|③ 实用文|📖|📄|⬇|‹|←|配套读物|理论母文|白话解释文|方法实践文|编者导语|全部作品|学员专栏|评分：|待独立|提升集中|本批|初评未达|思想拓展声明|人机分工声明)')
os.makedirs('ch',exist_ok=True)
meta=[]
for n,au,slug,d,title,sub,disc in CH:
    p=f"{BASE}{slug}/{d}/index.html"
    md=extract(p)
    lines=[]
    for l in md.split('\n'):
        s=l.strip()
        if not s: lines.append(''); continue
        if DROP.match(s.lstrip('#').strip()): continue
        if len(s)<40 and re.match(r'^#{3,5} ?$',s): continue
        lines.append(l)
    body='\n'.join(lines)
    body=re.sub(r'\n{3,}','\n\n',body).strip()
    body=body.replace('本文','本章').replace('本篇','本章')
    nz=len(re.findall(r'[\u4e00-\u9fff]',body))
    open(f'ch/ch{n:02d}.md','w').write(f"## 第{'一二三四五六七八九十'[n-1]}章　{title}\n\n*{sub}*\n\n> 原作者：{au}　｜　原文：学员专栏 · {slug}/{d}\n\n{body}\n")
    meta.append(dict(n=n,au=au,slug=slug,d=d,title=title,nz=nz))
    print(f"ch{n:02d} {au:5s} {title:12s} {nz:6d}")
json.dump(meta,open('meta.json','w'),ensure_ascii=False,indent=1)
print("十章合计",sum(m['nz'] for m in meta))
