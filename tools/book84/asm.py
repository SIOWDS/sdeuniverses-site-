import re,json
NAME={'chen-xiaoyan':'陈晓艳','yang-yong':'阳涌','ji-chunlei':'季春雷','gao-peng':'高鹏',
 'kong-fanhe':'孔凡鹤','zhang-qiong':'张琼','gao-yuhan':'高于涵','shao-min':'少敏',
 'hu-min':'胡敏','qin-li':'秦莉','hu-zhiying':'胡志英'}
SEL=json.load(open('selected.json'))
ORDER=['chen-xiaoyan','yang-yong','ji-chunlei','kong-fanhe','gao-peng','zhang-qiong',
       'gao-yuhan','shao-min','hu-min','qin-li','hu-zhiying']
TITLE=['主语不再是个人','一次成功由谁承载','自我可以被完美绕过',
       '被工艺除去的那道阻力','善失去了自己的语法','熄灭它的不是暴力，是拥抱',
       '带着全部信念盖下的那个章','越审越不能改','裁判席本身就是干扰',
       '押进去就拿不回来的那一部分','蚀先于生']
ORIG={'chen-xiaoyan':'预防如何不再以个人为主语','yang-yong':'一次成功由谁承载？',
 'ji-chunlei':'主体性代偿：一个关于"自我"如何被绕过的生成机制分析',
 'kong-fanhe':'生成性裂隙：营养生成论对现代营养学的发生学重构',
 'gao-peng':'善的语法消亡：强迫行善制度如何侵蚀道德主体的内在繁衍能力',
 'zhang-qiong':'配准性生成：长期成功团体的隐性担保与决断力基础的被改写',
 'gao-yuhan':'未善的代价：当"成为好人"变成一道工序',
 'shao-min':'越审越不能改：人工监督如何同时生产控制证据与控制失效',
 'hu-min':'裁定性干扰：为什么修复的判决动作本身即构成修复的结构性减损',
 'qin-li':'存押：艺术作为代偿时代中存在的不可逆赌注',
 'hu-zhiying':'蚀先于生：为什么形态的耗散比生成更原始'}
CN=['一','二','三','四','五','六','七','八','九','十','十一']
def demote(t):
    # 章内 ## 保持，### 保持；确保没有 # 一级
    return re.sub(r'(?m)^# (?!#)','## ',t)
def rd(p): return open(p,encoding='utf-8').read()
parts=[]
parts.append(rd('new/pub.md'))
parts.append(rd('new/au.md'))
parts.append(rd('new/qy.md'))
f2=rd('new/front2.md')
# front2 含 导读/导论/四编首，按 '# ' 切
segs=re.split(r'(?m)^(?=# )',f2)
segs=[s for s in segs if s.strip()]
DAODU,DAOLUN,B1,B2,B3,B4=segs
parts += [DAODU,DAOLUN,B1]
for i,k in enumerate(ORDER):
    if i==3: parts.append(rd('new/sn.md')); parts.append(B2)
    if i==6: parts.append(B3)
    if i==9: parts.append(rd('new/hz.md')); parts.append(B4)
    body=demote(rd('ch/%s.body.md'%k))
    # 去掉正文开头重复的原题一级/二级标题
    lines=body.split('\n')
    while lines and (not lines[0].strip() or lines[0].startswith('##') and ORIG[k][:6] in lines[0]):
        if lines[0].startswith('##') and ORIG[k][:6] in lines[0]: lines.pop(0)
        elif not lines[0].strip(): lines.pop(0)
        else: break
    body='\n'.join(lines)
    head='# 第%s章　%s\n\n> 本章原题《%s》，作者 %s，原文见 https://sdeuniverses.com/students/%s/\n' % (
        CN[i],TITLE[i],ORIG[k],NAME[k],SEL[k])
    parts.append(head+'\n'+body)
bk=re.split(r'(?m)^(?=# )',rd('new/back.md'))
bk=[s for s in bk if s.strip()]
JY,AP1,AP2,AP3,FD=bk
parts += [JY, rd('new/ref.md'), AP1,AP2,AP3, FD]
ms='\n\n'.join(p.strip()+'\n' for p in parts)
ms=re.sub(r'\n{4,}','\n\n\n',ms)
open('manuscript.md','w').write(ms)
cjk=sum(1 for c in ms if '\u4e00'<=c<='\u9fff')
print('部件数',len(parts),'| 全书汉字',cjk)
print('一级标题：')
for l in ms.split('\n'):
    if l.startswith('# '): print('  ',l[2:60])
