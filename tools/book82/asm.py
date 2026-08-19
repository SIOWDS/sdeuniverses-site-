import re,json
CN="零一二三四五六七八九十"
def rd(p): return open(p,encoding='utf-8').read().strip()
def cn(n): return CN[n] if n<10 else ("十"+(CN[n%10] if n%10 else ""))

ip=[p.strip() for p in re.split(r'\n---\n',rd('front/intro.md')) if p.strip()]
assert len(ip)==5
ch=[rd(f'ch/ch{i:02d}.md') for i in range(1,11)]

# 参考书目
refs=json.load(open('refs.json'))
L=['# 参考书目','','本表按章合并自各章原有文献表，未作增删；各章引注编号为该章原编号，与本表次序不对应。']
for i,title,items in refs:
    L += ['', '## 第'+cn(i)+'章　'+title, '']
    L += ['\n\n'.join(x.strip() for x in items)]
REF='\n'.join(L)

# 附录切三篇
ap=[p.strip() for p in re.split(r'\n---\n',rd('back/appendix.md')) if p.strip()]
assert len(ap)==3, len(ap)

parts=[
 rd('front/titlepage.md'), rd('front/pub.md'), rd('front/author.md'),
 rd('front/qianyan.md'), rd('front/daodu.md'), ip[0],
 ip[1], ch[0], ch[1], ch[2],
 rd('front/hub.md'),
 ip[2], ch[3], ch[4], ch[5],
 ip[3], ch[6], ch[7],
 ip[4], ch[8], ch[9],
 rd('back/merge.md'), rd('back/jieyu.md'),
 REF, ap[0], ap[1], ap[2],
 rd('back/houji.md'), rd('back/goldlines.md'), rd('back/fengdi.md'),
]
KEEP={7,8,9,10,12,13,14,16,17,19,20,21}   # 章 / 枢纽章 / 合章
parts=[p if i in KEEP else re.sub(r'^## ','### ',p,flags=re.M) for i,p in enumerate(parts)]
ms='\n\n'.join(parts)
open('manuscript.md','w').write(ms)
print('部件',len(parts),'汉字',len(re.findall(r'[\u4e00-\u9fff]',ms)))
print('# 级：')
for m in re.finditer(r'^# (.+)$',ms,re.M): print('   ',m.group(1)[:34])
print('## 级：',len(re.findall(r'^## ',ms,re.M)))
