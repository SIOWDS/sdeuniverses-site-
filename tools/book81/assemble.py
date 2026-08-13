import re,json,os
S='src/'
def rd(p): return open(S+p,encoding='utf-8').read()
def blk(txt,tag):
    m=re.search(r'^'+tag+r'\n(.*?)\n'+tag+r'_END',txt,re.S|re.M)
    return m.group(1).strip()
def part(txt,tag):
    m=re.search(r'^'+tag+r'\n(.*?)(?=\nPART\d|\Z)',txt,re.S|re.M)
    return m.group(1).strip()

b1=rd('back1.md'); b2=rd('back2.md'); pt=rd('parts.md')
refs=json.load(open(S+'refs.json'))
CN="零一二三四五六七八九十"
def cn(n): return CN[n] if n<10 else ("十"+(CN[n%10] if n%10 else ""))

reflines=['# 参考文献','','本表按章合并自各章原有文献表，未作增删。']
for i,title,body in refs:
    reflines.append('')
    reflines.append('## 第'+cn(i)+'章　'+title)
    reflines.append('')
    reflines.append('\n\n'.join(x.strip() for x in body.split('\n') if x.strip()))
REF='\n'.join(reflines)

parts=[
 '# 答案随时可得之后\n\n**论知识不是存量，及重新推出它的那一段为何不入账**\n\n王德生 ＋ Claude 著\n\n德麦国际出版社 · 专著第 81 号',
 blk(b2,'PUB'),
 blk(b2,'AUTHOR'),
 rd('reviews.md'),
 blk(b1,'QIANYAN'),
 blk(b1,'DAODU'),
 rd('intro.md'),
 part(pt,'PART1'), rd('ch01.md'), rd('ch02.md'), rd('ch03.md'),
 rd('hub.md'),
 part(pt,'PART2'), rd('ch04.md'), rd('ch05.md'), rd('ch06.md'),
 part(pt,'PART3'), rd('ch07.md'), rd('ch08.md'),
 part(pt,'PART4'), rd('ch09.md'), rd('ch10.md'),
 rd('hz.md'),
 blk(b1,'JIEYU'),
 REF,
 blk(b2,'AP1'), blk(b2,'AP2'), blk(b2,'AP3'),
 blk(b2,'HOUJI'),
 blk(b2,'FENGDI'),
]
import re as _re
def demote(x):
    return _re.sub(r'^## ', '### ', x, flags=_re.M)
# 章与枢纽章/合章保留 ## ；其余部件的 ## 一律降为 ###
KEEP={7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22}
parts=[demote(p) if i not in KEEP else p for i,p in enumerate(parts)]
doc='\n\n'.join(p.strip() for p in parts)+'\n'
open('/mnt/user-data/outputs/答案随时可得之后_稿本v1.md','w',encoding='utf-8').write(doc)
open('manuscript.md','w',encoding='utf-8').write(doc)
han=len(re.findall(r'[\u4e00-\u9fff]',doc))
print('汉字',han)
print('一级标题',len(re.findall(r'^# ',doc,re.M)),'二级',len(re.findall(r'^## ',doc,re.M)),'三级',len(re.findall(r'^### ',doc,re.M)))
