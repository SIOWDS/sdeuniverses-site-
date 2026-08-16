import re,json
ORDER=['chen-xiaoyan','yang-yong','ji-chunlei','kong-fanhe','gao-peng','zhang-qiong',
       'gao-yuhan','shao-min','hu-min','qin-li','hu-zhiying']
NAME={'chen-xiaoyan':'陈晓艳','yang-yong':'阳涌','ji-chunlei':'季春雷','gao-peng':'高鹏',
 'kong-fanhe':'孔凡鹤','zhang-qiong':'张琼','gao-yuhan':'高于涵','shao-min':'少敏',
 'hu-min':'胡敏','qin-li':'秦莉','hu-zhiying':'胡志英'}
REFHEAD=re.compile(r'^##+\s*(参考文献|经编辑核验的参考文献|本次打磨所核验的文献|编辑增补所依据的核验文献|本轮定稿所核验的文献|本次深化所核验的文献)\s*$')
allrefs={}; kept={}
for k in ORDER:
    t=open('ch/%s.clean.md'%k,encoding='utf-8').read()
    lines=t.split('\n'); out=[]; refs=[]; mode=False
    for l in lines:
        if l.startswith('#'):
            mode = bool(REFHEAD.match(l))
            if mode: continue
        if mode:
            s=l.strip()
            if s: refs.append(re.sub(r'^\s*[\[\(]?\d+[\]\)\.、]\s*','',s))
        else: out.append(l)
    body='\n'.join(out); body=re.sub(r'\n{3,}','\n\n',body).strip()+'\n'
    open('ch/%s.body.md'%k,'w').write(body)
    # 去掉表格行与空壳
    refs=[r for r in refs if len(r)>12 and not r.startswith('|')]
    allrefs[k]=refs
    kept[k]=sum(1 for c in body if '\u4e00'<=c<='\u9fff')
    print(f'{NAME[k]:5s} 正文汉字{kept[k]:6d}  文献{len(refs):4d} 条')
json.dump(allrefs,open('refs.json','w'),ensure_ascii=False,indent=1)
print('文献合计', sum(len(v) for v in allrefs.values()), '| 正文合计', sum(kept.values()))
