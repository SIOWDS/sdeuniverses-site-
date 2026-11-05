#!/usr/bin/env python3
# 按第 220、302 号封面版式做《接、不接与没接》封面封底：900×1270，另出 2 倍图
import asyncio
from playwright.async_api import async_playwright
BG='linear-gradient(180deg,#0F1B3A 0%,#1B2A5A 100%)'
CREAM='#F3E9D6';GOLD='#D9A441';TEAL='#2FA8B8';TAN='#D5C5A0'
ISBN='9798906906014'
def ean13_svg(code,x0,y0,mod=2.0,h=92):
    L=['0001101','0011001','0010011','0111101','0100011','0110001','0101111','0111011','0110111','0001011']
    G=['0100111','0110011','0011011','0100001','0011101','0111001','0000101','0010001','0001001','0010111']
    R=['1110010','1100110','1101100','1000010','1011100','1001110','1010000','1000100','1001000','1110100']
    P=['LLLLLL','LLGLGG','LLGGLG','LLGGGL','LGLLGG','LGGLLG','LGGGLL','LGLGLG','LGLGGL','LGGLGL']
    assert (10-sum(int(c)*(3 if i%2 else 1) for i,c in enumerate(code[:12]))%10)%10==int(code[12])
    pat=P[int(code[0])];s='101'
    for i,c in enumerate(code[1:7]):s+=(L if pat[i]=='L' else G)[int(c)]
    s+='01010'
    for c in code[7:]:s+=R[int(c)]
    s+='101'
    out=[]
    for i,b in enumerate(s):
        if b=='1':
            guard=i<3 or 45<=i<50 or i>=92
            out.append(f'<rect x="{x0+i*mod:.2f}" y="{y0}" width="{mod}" height="{h+(8 if guard else 0)}" fill="#000"/>')
    return ''.join(out)
def drop(x,y,s,fill,op=1):
    return f'<path transform="translate({x},{y}) scale({s})" fill="{fill}" opacity="{op}" d="M0,-30 C9,-12 19,-1 19,12 A19,19 0 1 1 -19,12 C-19,-1 -9,-12 0,-30 Z"/>'
def art():
    o=[f'<circle cx="625" cy="800" r="300" fill="none" stroke="{GOLD}" stroke-width="3" opacity=".62"/>']
    # 接：落进桶里的水滴
    o+=[drop(632,560,.62,CREAM),drop(648,618,.72,TEAL)]
    # 桶
    o.append(f'<path d="M545,712 A92,110 0 0 1 735,712" fill="none" stroke="{TAN}" stroke-width="7"/>')
    o.append(f'<path d="M542,712 L738,712 L712,930 L568,930 Z" fill="{CREAM}"/>')
    o.append(f'<ellipse cx="640" cy="712" rx="98" ry="17" fill="#16244F" stroke="{CREAM}" stroke-width="6"/>')
    o.append(f'<ellipse cx="640" cy="715" rx="84" ry="10" fill="{TEAL}"/>')
    o.append(f'<path d="M552,778 L728,778 L725,800 L555,800 Z" fill="{TAN}"/><path d="M561,866 L719,866 L716,888 L564,888 Z" fill="{TAN}"/>')
    # 不接：落在桶外的水滴，落地
    o+=[drop(462,700,.62,CREAM),drop(442,782,.72,CREAM),drop(426,868,.56,CREAM,.9)]
    o.append(f'<ellipse cx="420" cy="932" rx="46" ry="8" fill="{CREAM}" opacity=".9"/>')
    # 地面
    o.append(f'<rect x="350" y="940" width="510" height="13" rx="6.5" fill="{GOLD}"/>')
    # 沉底：地面之下，越沉越淡
    for x,y,r,a in ((420,978,8,.95),(432,1006,6.5,.72),(416,1032,5,.5),(428,1054,3.8,.32)):
        o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GOLD}" opacity="{a}"/>')
    # 没接：桶外还没落定的散点
    for x,y,r,a in ((812,610,3,.45),(834,652,3.5,.55),(802,694,4.5,.7),(842,728,5,.8),(806,772,6,.9),(838,820,7,1),(800,866,8.5,1)):
        o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GOLD}" opacity="{a}"/>')
    return ''.join(o)
BASE=f'''<!doctype html><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:900px;height:1270px;overflow:hidden}}
body{{background:{BG};position:relative;font-family:"Noto Sans CJK SC",sans-serif;color:#fff}}
.a{{position:absolute}}svg{{position:absolute;left:0;top:0}}
.serif{{font-family:"Noto Serif CJK SC",serif}}
</style>'''
FRONT=BASE+f'''<svg width="900" height="1270" viewBox="0 0 900 1270">{art()}
<line x1="60" y1="1040" x2="390" y2="1040" stroke="{CREAM}" stroke-width="1.2" opacity=".55"/>
<line x1="410" y1="1068" x2="880" y2="1068" stroke="{CREAM}" stroke-width="1.2" opacity=".55"/></svg>
<div class="a serif" style="left:60px;top:186px;font-size:118px;font-weight:700;color:{CREAM};letter-spacing:0;line-height:1.15;white-space:nowrap">接<span style="margin-right:-50px">、</span>不接与没接</div>
<div class="a" style="left:62px;top:346px;font-size:27px;color:{GOLD};letter-spacing:1px">一样东西凭什么稳得住</div>
<div class="a" style="left:60px;top:1066px;font-size:32px;color:{CREAM};letter-spacing:3px;white-space:pre">王德生　黄倩盈　著</div>
<div class="a" style="left:60px;top:1164px;font-size:25px;font-weight:700;color:{CREAM};letter-spacing:1px">德麦国际出版社</div>
<div class="a" style="left:60px;top:1204px;font-size:15px;color:#B8BCCB;letter-spacing:3px">Demai International Press</div>'''
J=['一样东西稳得住，','不是差都调回来了，','不是它靠的都还在，','也不是样子演住了，','而是每一笔差都有去处。']
B=['一台恒温热水器，一桌吃饭的人，一部《中论》。','这本书把三本不搭界的书摆上一张桌子，','问同一件事：说“没事”的时候，那些差去了哪儿？','接，不接，没接。不接的差轮不回来，就沉成没接。','它还用公开代码查了自己两回：','一回没有得到支持，一回判不了，都写在书里。']
BACK=BASE+f'''<svg width="900" height="1270" viewBox="0 0 900 1270"><circle cx="720" cy="245" r="232" fill="none" stroke="{GOLD}" stroke-width="3" opacity=".6"/>
<line x1="70" y1="1086" x2="430" y2="1086" stroke="{CREAM}" stroke-width="1.2" opacity=".5"/>
<rect x="600" y="1038" width="240" height="192" fill="#fff"/>
<text x="720" y="1062" text-anchor="middle" font-family="Noto Sans CJK SC" font-size="13.5" fill="#000">ISBN 979-8-90690-601-4</text>
{ean13_svg(ISBN,625,1072,mod=2.0,h=112)}
<text x="720" y="1218" text-anchor="middle" font-family="Noto Sans CJK SC" font-size="15" letter-spacing="1.5" fill="#000">{ISBN}</text></svg>
<div class="a" style="left:70px;top:112px;font-size:31px;font-weight:700;line-height:52px;color:#fff">{'<br>'.join(J)}</div>
<div class="a" style="left:70px;top:420px;font-size:24px;line-height:45px;color:#E8E9F0">{'<br>'.join(B)}</div>
<div class="a" style="left:70px;top:752px;font-size:25px;color:{GOLD};white-space:pre">稳住的，都是挑着接的。放下的，会沉底。　　——本书</div>
<div class="a" style="left:70px;top:1106px;font-size:18px;line-height:36px;color:#D5D8E4">德麦国际出版社 · Demai International Press<br>德麦国际专著第 579 号<br>定价：US$20.00</div>'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        for name,html in (('cover',FRONT),('backcover',BACK)):
            for sc,suf in ((1,''),(2,'@2x')):
                pg=await b.new_page(viewport={'width':900,'height':1270},device_scale_factor=sc)
                await pg.set_content(html);await pg.wait_for_timeout(300)
                await pg.screenshot(path=f'{name}{suf}.png');await pg.close()
        await b.close()
asyncio.run(main())
from PIL import Image
for n in ('cover','backcover'):
    for s in ('','@2x'):
        Image.open(f'{n}{s}.png').convert('RGB').save(f'{n}{s}.jpg',quality=93)
a,b=[Image.open(f'{n}.png').convert('RGB') for n in ('cover','backcover')]
m=Image.new('RGB',(1810,1270),'#888');m.paste(a,(0,0));m.paste(b,(910,0));m.save('/tmp/claude-0/-home-claude/af5fd17d-dbae-5621-a899-df2f4c0f302c/scratchpad/cov/ours.png')
