import re,json,os
ORDER=['chen-xiaoyan','yang-yong','ji-chunlei','gao-peng','kong-fanhe','zhang-qiong',
       'gao-yuhan','shao-min','hu-min','qin-li','hu-zhiying']
NAME={'chen-xiaoyan':'陈晓艳','yang-yong':'阳涌','ji-chunlei':'季春雷','gao-peng':'高鹏',
 'kong-fanhe':'孔凡鹤','zhang-qiong':'张琼','gao-yuhan':'高于涵','shao-min':'少敏',
 'hu-min':'胡敏','qin-li':'秦莉','hu-zhiying':'胡志英'}
SEL=json.load(open('selected.json'))
rows=[]
for k in ORDER:
    t=open('ch/%s.md'%k,encoding='utf-8').read()
    # 1 删三联导航行（含 ① 理论母文 的整行）
    t='\n'.join(l for l in t.split('\n') if '理论母文' not in l)
    # 2 删纯 HTML 标签行
    t='\n'.join(l for l in t.split('\n') if not re.fullmatch(r'\s*</?(div|span|section|p|a)[^>]*>\s*',l))
    # 3 行内标签清除
    t=re.sub(r'</?span[^>]*>','',t)
    t=re.sub(r'</?div[^>]*>','',t)
    t=re.sub(r'<a [^>]*>|</a>','',t)
    t=re.sub(r'\{[^{}\n]*\}','',t)          # pandoc 属性块
    # 4 站内自指
    t=t.replace('本文','本章').replace('本篇','本章')
    # 5 网页家具残词
    for w in ['📖 长文阅读','📄 在线 PDF','⬇ 下载 PDF','← 全部作品','‹ 全部作品','读全文']:
        t=t.replace(w,'')
    # 6 标题层级：原文 h1 降级、章标题稍后统一加
    t=re.sub(r'(?m)^# (?!#)','## ',t)
    t=re.sub(r'\n{3,}','\n\n',t).strip()+'\n'
    open('ch/%s.clean.md'%k,'w').write(t)
    cjk=sum(1 for c in t if '\u4e00'<=c<='\u9fff')
    raw=len(re.findall(r'<[a-zA-Z/][^>]*>',t))
    rows.append((NAME[k],cjk,raw,t.count('\n## ')))
for r in rows: print(f'{r[0]:5s} 汉字{r[1]:6d}  残留标签{r[2]:3d}  二级节{r[3]:3d}')
print('合计汉字', sum(r[1] for r in rows))
